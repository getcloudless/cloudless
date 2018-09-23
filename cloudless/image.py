"""
Cloudless Image

This component should allow for intuitive and transparent control over images, which are the top
level containers for services.
"""
from cloudless.log import logger
from cloudless.providers import get_provider
from cloudless.types.common import Image, Service
from cloudless.util.exceptions import DisallowedOperationException

class ImageClient:
    """
    Cloudless Image Client.

    This is the object through which all image related calls are made.  The objects returned by
    these commands are of type `cloudless.types.common.Image`.

    Usage:

        import cloudless
        client = cloudless.Client(provider, credentials)
        network = client.network.get("dev")
        service = client.service.get(network, "image-build")
        client.image.create("myimage", service)
        client.image.get("myimage")
        client.image.list()
        client.image.destroy(client.image.get("myimage"))

    The above commands will create and destroy a image named "image".
    """
    def __init__(self, provider, credentials):
        self.image = get_provider(provider).image.ImageClient(
            credentials)

    def create(self, name, service):
        """
        Create new image named "name" from "service".

        Example:

            client.image.create("myimage", service)

        """
        logger.debug('Creating image %s from service %s', name, service)
        if not isinstance(service, Service):
            raise DisallowedOperationException(
                "Service argument to create must be of type cloudless.types.common.Service")
        return self.image.create(name, service)

    def get(self, name):
        """
        Get a image named "name" and return some data about it.

        Example:

            client.image.get("myimage")

        """
        logger.debug('Getting image %s', name)
        return self.image.get(name)

    def destroy(self, image):
        """
        Destroy the given image.

        Example:

            client.image.destroy(client.image.get("myimage"))

        """
        logger.debug('Destroying image %s', image)
        if not isinstance(image, Image):
            raise DisallowedOperationException(
                "Argument to destroy must be of type cloudless.types.common.Image")
        return self.image.destroy(image)

    def list(self):
        """
        List all images.

        Example:

            client.image.list()

        """
        logger.debug('Listing images')
        return self.image.list()
