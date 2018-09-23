"""
Cloudless Image on GCE

This component should allow for intuitive and transparent control over images, which are the top
level containers for groups of instances/services.  This is the GCE implementation.
"""
from cloudless.util.exceptions import (BadEnvironmentStateException, DisallowedOperationException)
from cloudless.providers.gce.driver import get_gce_driver
from cloudless.providers.gce.log import logger
from cloudless.types.common import Image


class ImageClient:
    """
    Cloudless Image Client Object for GCE

    This is the object through which all image related calls are made for GCE.
    """

    def __init__(self, credentials):
        self.credentials = credentials
        self.driver = get_gce_driver(credentials)

    # pylint: disable=unused-argument
    def create(self, name, service):
        """
        Create new image named "name" from "service".
        """
        instances = [instance for subnetwork in service.subnetworks
                     for instance in subnetwork.instances]
        for gce_node in self.driver.list_nodes():
            if gce_node.uuid == instances[0].instance_id:
                node = gce_node
        if not node:
            raise BadEnvironmentStateException("Could not find instance in service %s" % service)
        if len(node.extra["disks"]) != 1:
            raise DisallowedOperationException(
                "Only support exactly one volume for image create: %s" % node.extra["disks"])
        logger.info("Stopping node: %s", node.name)
        self.driver.ex_stop_node(node)

        logger.info("Creating image from service: %s", service.name)
        volume = self.driver.ex_get_volume(node.extra["disks"][0]["deviceName"])
        image = self.driver.ex_create_image(name, volume)
        logger.info("Created image: %s", image.id)
        return Image(name=image.name, image_id=image.id,
                     created_at=str(image.extra["creationTimestamp"]))

    def get(self, name):
        """
        Get a image named "name" and return some data about it.
        """
        for image in self.list():
            if image.name == name:
                logger.debug("Got image: %s", image)
                return image
        return None

    def destroy(self, image):
        """
        Destroy a image given by "image".
        """
        for gce_image in self.driver.list_images(self.driver.project):
            logger.debug("Raw image destroy: %s", gce_image)
            if gce_image.id == image.image_id:
                logger.debug("Destroying image: %s", gce_image)
                return self.driver.ex_delete_image(gce_image)
        return None

    def list(self):
        """
        List all images.
        """
        images = []
        for gce_image in self.driver.list_images(self.driver.project):
            logger.debug("Raw image list: %s", gce_image)
            images.append(Image(name=gce_image.name, image_id=gce_image.id,
                                created_at=str(gce_image.extra["creationTimestamp"])))
        return images
