"""
Cloudless Service on AWS

This is the AWS implmentation for the service API, a high level interface to manage groups of
instances.
"""
import time
import json
import itertools
import requests
import dateutil.parser
from botocore.exceptions import ClientError

from cloudless.util.blueprint import ServiceBlueprint
from cloudless.util.instance_fitter import get_fitting_instance
from cloudless.util.exceptions import (BadEnvironmentStateException,
                                       OperationTimedOut)
import cloudless.providers.aws.impl.network
import cloudless.providers.aws.impl.subnetwork
from cloudless.providers.aws.impl.asg import (ASG, AsgName)
from cloudless.providers.aws.impl.security_groups import SecurityGroups
from cloudless.providers.aws.schemas import (canonicalize_instance_info,
                                             canonicalize_node_size)
from cloudless.types.common import Service
from cloudless.providers.aws.log import logger

RETRY_COUNT = int(60)
RETRY_DELAY = float(10.0)


class ServiceClient:
    """
    Client object to manage instances.
    """

    def __init__(self, driver, credentials, mock=False):
        self.driver = driver
        self.credentials = credentials
        self.mock = mock
        self.subnetwork = cloudless.providers.aws.impl.subnetwork.SubnetworkClient(driver,
                                                                                   credentials,
                                                                                   mock)
        self.network = cloudless.providers.aws.impl.network.NetworkClient(driver, credentials)
        self.asg = ASG(driver, credentials)
        self.security_groups = SecurityGroups(driver, credentials)

    # pylint: disable=too-many-arguments, too-many-locals
    def create(self, network, service_name, blueprint, template_vars=None, count=None):
        """
        Create a group of instances in "network" named "service_name" with blueprint file at
        "blueprint".
        """
        # Load the service blueprint first so we check if it's valid.
        service_blueprint = ServiceBlueprint.from_file(blueprint)
        runtime_scripts = service_blueprint.runtime_scripts(template_vars)

        # Create the subnet we will deploy into.
        subnet_ids = [subnet_info.subnetwork_id for subnet_info
                      in self.subnetwork.create(network, service_name,
                                                blueprint=blueprint)]

        # Security Group
        asg_name = AsgName(network=network.name, subnetwork=service_name)
        vpc_id = network.network_id
        security_group_id = self.security_groups.create(str(asg_name), vpc_id)

        # Launch Configuration
        def lookup_ami(ami_name):
            ec2 = self.driver.client("ec2")
            images = ec2.describe_images(Filters=[{"Name": "name",
                                                   "Values": [ami_name]}])
            result_image = None
            for image in images["Images"]:
                if not result_image:
                    result_image = image
                if (dateutil.parser.parse(image["CreationDate"]) >
                        dateutil.parser.parse(result_image["CreationDate"])):
                    result_image = image
            return result_image["ImageId"]

        def create_launch_configuration(asg_name, service_blueprint, runtime_scripts):
            ami_id = lookup_ami(service_blueprint.image())
            associate_public_ip = service_blueprint.public_ip()
            instance_type = get_fitting_instance(self, service_blueprint)
            autoscaling = self.driver.client("autoscaling")
            autoscaling.create_launch_configuration(
                LaunchConfigurationName=str(asg_name), ImageId=ami_id,
                SecurityGroups=[security_group_id], UserData=runtime_scripts,
                AssociatePublicIpAddress=associate_public_ip,
                InstanceType=instance_type)
        create_launch_configuration(asg_name, service_blueprint, runtime_scripts)

        # Auto Scaling Group
        if count:
            instance_count = count
        else:
            instance_count = service_blueprint.availability_zone_count()
        autoscaling = self.driver.client("autoscaling")
        autoscaling.create_auto_scaling_group(
            AutoScalingGroupName=str(asg_name),
            LaunchConfigurationName=str(asg_name), MinSize=instance_count,
            MaxSize=instance_count, DesiredCapacity=instance_count,
            VPCZoneIdentifier=",".join(subnet_ids), LoadBalancerNames=[],
            HealthCheckType='ELB', HealthCheckGracePeriod=120)

        def wait_until(state):
            asg = self.get(network, service_name)

            def instance_list(service, state):
                return [instance for subnetwork in service.subnetworks
                        for instance in subnetwork.instances
                        if instance.state == state]

            retries = 0
            while len(instance_list(asg, state)) < instance_count:
                logger.info("Waiting for instance creation for service %s.  %s of %s running",
                            service_name, len(instance_list(asg, state)), instance_count)
                logger.debug("Waiting for instance creation in asg: %s", asg)
                asg = self.get(network, service_name)
                retries = retries + 1
                if retries > RETRY_COUNT:
                    raise OperationTimedOut("Timed out waiting for ASG to be created")
                time.sleep(RETRY_DELAY)
            logger.info("Success!  %s of %s instances running.", len(instance_list(asg, state)),
                        instance_count)
        wait_until("running")

        return self.get(network, service_name)

    def list(self):
        """
        List all instance groups.
        """
        services = []
        subnetworks = self.subnetwork.list()
        for network_name, subnetwork_info in subnetworks.items():
            for subnetwork_name, _ in subnetwork_info["subnetworks"].items():
                services.append(self.get(self.network.get(network_name), subnetwork_name))
        return services

    def _discover_asg(self, network_name, service_name):
        """
        Discover an autoscaling group given a network and service name.
        """
        autoscaling = self.driver.client("autoscaling")
        logger.debug("Discovering auto scaling groups with name: %s", service_name)
        asg_name = AsgName(network=network_name, subnetwork=service_name)
        asgs = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=[str(asg_name)])
        logger.debug("Found asgs: %s", asgs)
        if len(asgs["AutoScalingGroups"]) > 1:
            raise BadEnvironmentStateException(
                "Expected to find at most one auto scaling group "
                "named: %s, output: %s" % (str(asg_name), asgs))
        if not asgs["AutoScalingGroups"]:
            return None
        return asgs["AutoScalingGroups"][0]

    def get(self, network, service_name):
        """
        Discover a service in "network" named "service_name".
        """
        logger.debug("Discovering autoscaling group named %s in network: %s",
                     service_name, network)

        def discover_instances(instance_ids):
            """
            Given instance IDs get the actual instance data for them.
            """
            ec2 = self.driver.client("ec2")
            logger.debug("Discovering instances: %s", instance_ids)
            instances = {"Reservations": []}
            # Need this check because if we pass an empty list the API returns all instances
            if instance_ids:
                instances = ec2.describe_instances(InstanceIds=instance_ids)
            return [instance
                    for reservation in instances["Reservations"]
                    for instance in reservation["Instances"]]

        def add_instances_to_subnetwork_list(network, service_name, subnetworks):
            """
            Add the instances for this service to the list of subnetworks.  Returns the same
            subnetwork list with the instances added.
            """
            # 1. Get List Of Instances.
            discovery_retries = 0
            discovery_complete = False
            while discovery_retries < RETRY_COUNT:
                try:
                    asg = self._discover_asg(network.name, service_name)
                    if not asg:
                        return subnetworks
                    instance_ids = [instance["InstanceId"] for instance in asg["Instances"]]
                    instances = discover_instances(instance_ids)
                    logger.debug("Discovered instances: %s", instances)
                    discovery_complete = True
                except ClientError as client_error:
                    # There is a race between when I discover the autoscaling group
                    # itself and when I try to search for the instances inside it,
                    # so just retry if this happens.
                    logger.debug("Recieved exception discovering instance: %s", client_error)
                    if client_error.response["Error"]["Code"] == "InvalidInstanceID.NotFound":
                        pass
                    else:
                        raise

                if discovery_complete:
                    break
                discovery_retries = discovery_retries + 1
                logger.debug("Instance discovery retry number: %s", discovery_retries)
                if discovery_retries >= RETRY_COUNT:
                    raise OperationTimedOut(
                        "Exceeded retries while discovering %s, in network %s" %
                        (service_name, network))
                time.sleep(RETRY_DELAY)

            # 2. Add instances to subnets.
            # NOTE: In moto instance objects do not include a "SubnetId" and the IP addresses are
            # assigned randomly in the VPC, so for now just stripe instances across subnets.
            if self.mock:
                for instance, subnetwork, in zip(instances, itertools.cycle(subnetworks)):
                    subnetwork.instances.append(canonicalize_instance_info(instance))
                return subnetworks
            for subnetwork in subnetworks:
                for instance in instances:
                    if "SubnetId" in instance and subnetwork.subnetwork_id == instance["SubnetId"]:
                        subnetwork.instances.append(canonicalize_instance_info(instance))
            return subnetworks

        # 1. Get List Of subnetworks.  The service exists iff this exists.
        subnetworks = self.subnetwork.get(network, service_name)
        if not subnetworks:
            return None

        # 2. Add instances to subnetworks.
        subnetworks = add_instances_to_subnetwork_list(network, service_name, subnetworks)

        # 3. Profit!
        return Service(network=network, name=service_name, subnetworks=subnetworks)


    def destroy(self, service):
        """
        Destroy a group of instances described by "service".
        """
        logger.debug("Attempting to destroy: %s", service)
        asg_name = AsgName(network=service.network.name, subnetwork=service.name)

        asg = self._discover_asg(service.network.name, service.name)
        if asg:
            self.asg.destroy_auto_scaling_group_instances(asg_name)

        # Wait for instances to be gone.  Need to do this before we can delete
        # the actual ASG otherwise it will error.
        def instance_list(service, state):
            return [instance for subnetwork in service.subnetworks
                    for instance in subnetwork.instances
                    if instance.state != state]

        service = self.get(service.network, service.name)
        logger.debug("Found service: %s", service)
        retries = 0
        while service and instance_list(service, "terminated"):
            logger.info("Waiting for instance termination in service %s.  %s still terminating",
                        service.name, len(instance_list(service, "terminated")))
            logger.debug("Waiting for instance termination in asg: %s", service)
            service = self.get(service.network, service.name)
            retries = retries + 1
            if retries > RETRY_COUNT:
                raise OperationTimedOut("Timed out waiting for ASG scale down")
            time.sleep(RETRY_DELAY)
        logger.info("Success!  All instances terminated.")

        asg = self._discover_asg(service.network.name, service.name)
        if asg:
            self.asg.destroy_auto_scaling_group(asg_name)

        # Wait for ASG to be gone.  Need to wait for this because it's a dependency of the launch
        # configuration.
        asg = self._discover_asg(service.network.name, service.name)
        retries = 0
        while asg:
            logger.debug("Waiting for asg deletion: %s", asg)
            asg = self._discover_asg(service.network.name, service.name)
            retries = retries + 1
            if retries > RETRY_COUNT:
                raise OperationTimedOut("Timed out waiting for ASG deletion")
            time.sleep(RETRY_DELAY)

        vpc_id = service.network.network_id
        lc_security_group = self.asg.get_launch_configuration_security_group(
            service.network.name, service.name)
        self.asg.destroy_launch_configuration(asg_name)
        if lc_security_group:
            logger.debug("Deleting referencing rules of sg: %s", lc_security_group)
            self.security_groups.delete_referencing_rules(vpc_id,
                                                          lc_security_group)
            logger.debug("Attempting to delete sg: %s", lc_security_group)
            self.security_groups.delete_with_retries(lc_security_group,
                                                     RETRY_COUNT, RETRY_DELAY)
        else:
            logger.debug("Attempting to delete sg by name: %s", str(asg_name))
            self.security_groups.delete_by_name(vpc_id, str(asg_name),
                                                RETRY_COUNT, RETRY_DELAY)

        self.subnetwork.destroy(service.network, service.name)

    def node_types(self):
        """
        Get a list of node sizes to use for matching resource requirements to
        instance type.
        """
        pricing = self.driver.client("pricing")

        filters = [
            {"Type":"TERM_MATCH", "Field":"ServiceCode", "Value":"AmazonEC2"},
            {"Type":"TERM_MATCH", "Field":"location", "Value":"US East (N. Virginia)"},
            {"Type":"TERM_MATCH", "Field":"instanceFamily", "Value":"General Purpose"},
            {"Type":"TERM_MATCH", "Field":"currentGeneration", "Value":"Yes"},
            {"Type":"TERM_MATCH", "Field":"operatingSystem", "Value":"Linux"},
            {"Type":"TERM_MATCH", "Field":"productFamily",
             "Value":"Compute Instance"},
            {"Type":"TERM_MATCH", "Field":"preinstalledSw", "Value":"NA"}
            ]
        next_token = ""
        node_sizes = []
        try:
            while True:
                products = pricing.get_products(ServiceCode="AmazonEC2",
                                                Filters=filters, NextToken=next_token)
                for node_info in products["PriceList"]:
                    node_sizes.append(
                        canonicalize_node_size(json.loads(node_info)["product"]["attributes"]))
                if "NextToken" not in products:
                    break
                next_token = products["NextToken"]
        except requests.exceptions.ConnectionError:
            # This happens in moto, this should probably figure out whether moto
            # is in use in a smarter way.
            return [{
                "type": "c4.8xlarge",
                "memory": 9999999999999,
                "cpus": 100
                }]
        return node_sizes
