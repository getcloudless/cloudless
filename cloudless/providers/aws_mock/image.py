"""
Cloudless Image on Mock AWS
"""
import boto3
from moto import mock_ec2, mock_autoscaling
import cloudless.providers.aws.impl.image

@mock_ec2
@mock_autoscaling
class ImageClient:
    """
    Cloudless Image Client Object for AWS

    This is the object through which all image related calls are made for AWS.
    """

    def __init__(self, credentials):
        self.image = cloudless.providers.aws.impl.image.ImageClient(boto3, credentials,
                                                                    mock=True)

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
