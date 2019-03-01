"""
Cloudless Image on Mock AWS
"""
import boto3
import cloudless.providers.aws.impl.image

class ImageClient:
    """
    Cloudless Image Client Object for AWS

    This is the object through which all image related calls are made for AWS.
    """

    def __init__(self, credentials):
        if "profile" in credentials:
            boto3.setup_default_session(profile_name=credentials["profile"])
        self.image = cloudless.providers.aws.impl.image.ImageClient(boto3, mock=True)

    def create(self, name, service):
        """
        Create new image named "name" from "service".
        """
        return self.image.create(name, service)

    # pylint: disable=no-self-use
    def get(self, name):
        """
        Get a image named "name" and return some data about it.
        """
        return self.image.get(name)

    # pylint: disable=no-self-use
    def destroy(self, image):
        """
        Destroy a image given the provided image object.
        """
        return self.image.destroy(image)

    # pylint: disable=no-self-use
    def list(self):
        """
        List all images.
        """
        return self.image.list()
