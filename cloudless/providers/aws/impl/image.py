"""
Cloudless Image on AWS

This component should allow for intuitive and transparent control over images, which are the top
level containers for groups of instances/services.  This is the AWS implementation.
"""
from retrying import retry
from cloudless.providers.aws.log import logger
from cloudless.util.exceptions import (OperationTimedOut, BadEnvironmentStateException,
                                       DisallowedOperationException)
from cloudless.types.common import Image
from cloudless.providers.aws.impl.asg import (ASG, AsgName)

RETRY_COUNT = 60
RETRY_DELAY = 5000

class ImageClient:
    """
    Cloudless Image Client Object for AWS

    This is the object through which all image related calls are made for AWS.
    """

    def __init__(self, driver, credentials, mock=False):
        self.driver = driver
        self.credentials = credentials
        self.mock = mock
        self.asg = ASG(driver, credentials)

    # pylint:disable=too-many-locals
    def create(self, name, service):
        """
        Create new image named "name" from "service".
        """
        ec2 = self.driver.client("ec2")
        instances = [instance for subnetwork in service.subnetworks
                     for instance in subnetwork.instances]
        if len(instances) != 1:
            raise DisallowedOperationException(
                "Service must have exactly one instance, found %s" % instances)

        def get_instance(instance_id):
            reservations = ec2.describe_instances(InstanceIds=[instance_id])
            raw_instances = [instance for reservation in reservations["Reservations"]
                             for instance in reservation["Instances"]]
            if len(raw_instances) != 1:
                raise DisallowedOperationException(
                    "Service must have exactly one instance, found %s" % raw_instances)
            return raw_instances[0]

        # First, stop instances to prevent the state from changing while we're snapshotting.
        logger.info("Stopping instance: %s", instances[0].instance_id)
        autoscaling = self.driver.client("autoscaling")

        # Must detach from autoscaling group otherwise our instance will get terminated.  See
        # https://stackoverflow.com/a/28883869.
        #
        # Also see https://github.com/getcloudless/cloudless/issues/20.
        def detach_from_asg(service, instance_id):
            asg_name = str(AsgName(network=service.network.name, subnetwork=service.name))
            autoscaling.update_auto_scaling_group(AutoScalingGroupName=asg_name, MinSize=0)
            self.asg.wait_for_in_service(asg_name, instance_id)
            autoscaling.detach_instances(InstanceIds=[instance_id], AutoScalingGroupName=asg_name,
                                         ShouldDecrementDesiredCapacity=True)
        detach_from_asg(service, instances[0].instance_id)

        def retry_if_timeout(exception):
            """
            Checks if this exception is just because we haven't converged yet.
            """
            return isinstance(exception, OperationTimedOut)

        ec2.stop_instances(InstanceIds=[instances[0].instance_id])
        @retry(wait_fixed=RETRY_DELAY, stop_max_attempt_number=RETRY_COUNT,
               retry_on_exception=retry_if_timeout)
        def wait_for_stopped(instance_id):
            raw_instance = get_instance(instance_id)
            logger.debug("Current state: %s", raw_instance)
            if raw_instance["State"]["Name"] != "stopped":
                raise OperationTimedOut("Timed out waiting for instance: %s to stop" % instance_id)
        wait_for_stopped(instances[0].instance_id)

        # Get information about the instance's block device
        def get_blockdev_info():
            raw_instance = get_instance(instances[0].instance_id)
            logger.debug("Getting blockdev info from: %s", raw_instance)
            if len(raw_instance["BlockDeviceMappings"]) != 1:
                raise DisallowedOperationException(
                    "Currently only support saving instances with one blockdev, found %s" % (
                        raw_instance))
            volume_id = raw_instance["BlockDeviceMappings"][0]["Ebs"]["VolumeId"]
            volumes = ec2.describe_volumes(VolumeIds=[volume_id])
            if len(volumes["Volumes"]) != 1:
                raise BadEnvironmentStateException(
                    "Found two volumes with the same id: %s" % volumes)
            volume = volumes["Volumes"][0]
            return {
                "DeviceName": raw_instance["BlockDeviceMappings"][0]["DeviceName"],
                "Ebs": {
                    "Encrypted": volume["Encrypted"],
                    "DeleteOnTermination": True,
                    "VolumeSize": volume["Size"],
                    "VolumeType": volume["VolumeType"]
                }}
        block_device = get_blockdev_info()

        # Save the image and return image data
        def get_image(image_id):
            images = ec2.describe_images(ImageIds=[image_id])
            if len(images["Images"]) != 1:
                raise BadEnvironmentStateException("Expected exactly one image, found %s" % images)
            return images["Images"][0]

        @retry(wait_fixed=RETRY_DELAY, stop_max_attempt_number=RETRY_COUNT,
               retry_on_exception=retry_if_timeout)
        def wait_for_available(image_id):
            image = get_image(image_id)
            logger.debug("Current image state: %s", image)
            if image["State"] != "available":
                raise OperationTimedOut(
                    "Timed out waiting for image %s to be available." % image_id)

        logger.info("Creating image from instance: %s", instances[0].instance_id)
        image_id = ec2.create_image(InstanceId=instances[0].instance_id, Name=name,
                                    BlockDeviceMappings=[block_device])
        wait_for_available(image_id["ImageId"])

        logger.info("Created image: %s", image_id["ImageId"])
        image = get_image(image_id["ImageId"])

        # Terminate the instance so it doesn't cause us to fail deleting our service.  This is
        # unfortunately brittle and if something fails before this point we'll be in this weird
        # state where the security group will have a dependency.  That's not acceptable, but really
        # it depends on fixing: https://github.com/getcloudless/cloudless/issues/20 because the ASG
        # only reports the running instances and that's how the service destroy discovers them.
        ec2.terminate_instances(InstanceIds=[instances[0].instance_id])
        return Image(image_id=image["ImageId"],
                     name=image["Name"],
                     created_at=image["CreationDate"])

    def get(self, name):
        """
        Get a image named "name" and return some data about it.
        """
        for image in self.list():
            if image.name == name:
                return image
        return None

    def destroy(self, image):
        """
        Destroy a image given the provided image object.
        """
        ec2 = self.driver.client("ec2")
        raw_images = ec2.describe_images(Owners=["self"])
        logger.debug("Images: %s", raw_images)
        snapshot_ids = []
        for raw_image in raw_images["Images"]:
            if raw_image["ImageId"] == image.image_id:
                for bdm in raw_image["BlockDeviceMappings"]:
                    snapshot_id = bdm.get("Ebs", {}).get("SnapshotId")
                    if snapshot_id:
                        snapshot_ids.append(snapshot_id)
        logger.info("Deregistering image: %s", image.image_id)
        ec2.deregister_image(ImageId=image.image_id)
        for snapshot_id in snapshot_ids:
            logger.info("Deleting snapshot: %s", snapshot_id)
            ec2.delete_snapshot(SnapshotId=snapshot_id)

        def retry_if_timeout(exception):
            """
            Checks if this exception is just because we haven't converged yet.
            """
            return isinstance(exception, OperationTimedOut)

        @retry(wait_fixed=RETRY_DELAY, stop_max_attempt_number=RETRY_COUNT,
               retry_on_exception=retry_if_timeout)
        def wait_for_destroyed(image_name):
            logger.info("Waiting for image: %s to be destroyed", image_name)
            if self.get(image.name):
                raise OperationTimedOut(
                    "Timed out waiting for image %s to be gone." % image_name)
            logger.info("Success, did not find image: %s", image_name)
        wait_for_destroyed(image.name)

        return True

    def list(self):
        """
        List all images.
        """
        ec2 = self.driver.client("ec2")
        raw_images = ec2.describe_images(Owners=["self"])
        logger.debug("Images: %s", raw_images)
        images = []
        for image in raw_images["Images"]:
            images.append(Image(image_id=image["ImageId"],
                                name=image["Name"],
                                created_at=image["CreationDate"]))
        return images
