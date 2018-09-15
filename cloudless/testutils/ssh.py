"""
Utilities for spinning up a machine with a temporary SSH key installed.

This is trickier than you might expect, for the core reason that everything that could possibly get
a new SSH key on the machine must be baked into the image.

For starters, the provider specific SSH setup depends on what is already installed on the image.
Take for example the AWS keypairs
(https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html).  For images already
supported by AWS, keypairs work fine, but for custom images special setup must be done to explicitly
pull down and set up the SSH keys using the instance metadata.

Second, even executing scripts at startup are custom features baked into the provided AMIs.  See:
https://stackoverflow.com/questions/26158411/amazon-ec2-custom-ami-not-running-bootstrap-user-data.

The GCE docs show a good example of all the steps that must actually be set up for a custom image:
https://cloud.google.com/compute/docs/images/import-existing-image.  No SSH keys or startup script
execution is included.

So in summary, everything related to setting up SSH access depends on whatever software is already
installed on the image.  Because of that, this library does not do any cloud specific key setup and
any frameworks that need SSH (like the blueprint test framework) must do it by passing predefined
template variables to the startup script.  This minimizes the cloud specific configuration to only
what is strictly necessary and lets the user control how to create those accounts.
"""
from Crypto.PublicKey import RSA
import attr

# pylint: disable=too-few-public-methods
@attr.s
class SSHKeyPair:
    """
    A holder for an SSH keypair.
    """
    public_key = attr.ib(type=str)
    private_key = attr.ib(type=str)

# pylint: disable=unused-argument
def generate_ssh_keypair():
    """
    Generates an SSH keypair.
    """
    key = RSA.generate(2048)
    pubkey = key.publickey()
    return SSHKeyPair(pubkey.exportKey('OpenSSH').decode(), key.exportKey('PEM').decode())
