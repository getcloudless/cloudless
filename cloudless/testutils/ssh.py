"""
Utilities for spinning up a machine with a temporary SSH key installed.

This is trickier than you might expect, for the core reason that everything that could possibly get
a new SSH key on the machine must be baked into the image.

For starters, the provider specific SSH setup depends on what is already installed on the image.
Take for example the AWS keypairs
(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html).  For images already
supported by AWS, keypairs work fine, but for custom images special setup must be done to explicitly
pull down and set up the SSH keys.  I haven't found anyone running into this yet explicitly, so I'd
have to verify myself, but I can't think of any other way it could possibly work.

Second, even executing scripts at startup are custom features baked into the provided AMIs.  See:
https://stackoverflow.com/questions/26158411/amazon-ec2-custom-ami-not-running-bootstrap-user-data.

The GCE docs show a good example of all the steps that must actually be set up for a custom image:
https://cloud.google.com/compute/docs/images/import-existing-image.  No SSH keys or startup script
execution is included.

So in summary, everything related to setting up SSH access depends on whatever software is already
installed on the image.  This means that anything injecting a temporary SSH keypair cross cloud and
in a way that can support custom images must be extremely flexible.
"""
from Crypto.PublicKey import RSA
import attr
from cloudless.types.common import Service
from cloudless.testutils.blueprint_tester import generate_unique_name

# pylint: disable=too-few-public-methods
@attr.s
class TestService:
    """
    A holder for an SSH keypair and test Service metadata.
    """
    service = attr.ib(type=Service)
    public_key = attr.ib(type=str)
    private_key = attr.ib(type=str)

# pylint: disable=unused-argument
def aws_keypair(client, network, blueprint):
    """
    Creates an instance with SSH set up using an AWS keypair.
    """
    service_name = generate_unique_name("ssh-test")
    key = RSA.generate(2048)
    pubkey = key.publickey()
    openssh_key = pubkey.exportKey('OpenSSH')
    test_service = client.service.create(network, service_name, blueprint, {}, count=1,
                                         proprietary_ssh_setup={"key_material": openssh_key})
    return TestService(test_service, openssh_key, key.exportKey('PEM').decode())

# pylint: disable=unused-argument
def gce_metadata(client, network, blueprint):
    """
    Creates an instance with SSH set up using GCE metadata.
    """
    raise NotImplementedError

# pylint: disable=unused-argument
def cloud_init_multipart(client, network, blueprint):
    """
    Creates an instance with SSH set up by prepending it to the user data in the blueprint with a
    cloud-init multipart file.
    """
    raise NotImplementedError

# pylint: disable=unused-argument
def cloud_init_reboot(client, network, blueprint):
    """
    Creates an instance with SSH set up using cloud init followed by a reboot with the real user
    data.
    """
    raise NotImplementedError

# pylint: disable=unused-argument
def script_reboot(client, network, blueprint):
    """
    Creates an instance with SSH set up using a script followed by a reboot with the real user data.
    """
    raise NotImplementedError

SSH_SETUP_METHODS = {
    "mock-aws": {
        "default": aws_keypair
        },
    "aws": {
        "default": aws_keypair
        },
    "gce": {
        "default": gce_metadata
        },
    "common": {
        "cloud-init-multipart": cloud_init_multipart,
        "cloud-init-reboot": cloud_init_reboot,
        "script-reboot": script_reboot
        }
    }

def create_test_instance(client, network, provider, blueprint, ssh_setup_method="provider-default"):
    """
    Creates a test instance and returns a temporary keypair that you can use to access the instance
    using the "admin" user.

    Returns the temporary keypair.
    """
    if ssh_setup_method == "provider-default":
        return SSH_SETUP_METHODS[provider]["default"](client, network, blueprint)
    return SSH_SETUP_METHODS["common"][ssh_setup_method](client, network, blueprint)
