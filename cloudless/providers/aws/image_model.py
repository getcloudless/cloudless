"""
Cloudless Image Model on AWS
"""
import boto3
import dateutil.parser
import cloudless.model
from cloudless.types.common import ImageModel
import cloudless.providers.aws.impl.image

class ImageResourceDriver(cloudless.model.ResourceDriver):
    """
    This class is what gets called when the user is trying to interact with a "Image" resource.
    """
    def __init__(self, provider, credentials):
        self.provider = provider
        self.credentials = credentials
        super(ImageResourceDriver, self).__init__(provider, credentials)
        if "profile" in credentials:
            boto3.setup_default_session(profile_name=credentials["profile"])
        self.driver = boto3

    def create(self, resource_definition):
        raise NotImplementedError("Image Creation Not Implemented")

    def apply(self, resource_definition):
        raise NotImplementedError("Image Application Not Implemented")

    def delete(self, resource_definition):
        raise NotImplementedError("Image Deletion Not Implemented")

    def get(self, resource_definition):
        image = resource_definition

        def lookup_image(ami_name):
            """
            Looks up the image.  The EC2 API supports simple wildcard matching.
            """
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
            return result_image

        # Get rid of this when I reimplement here, now just for compatibility/testing.
        # Also do not pass the blueprint.
        found_image = lookup_image(image.name)
        if found_image:
            return [ImageModel(version=image.version, name=found_image["Name"],
                               id=found_image["ImageId"])]
        return None

    def flags(self, resource_definition):
        return []
