"""
Class to manage an image build.
"""
import os
import subprocess
import json
from functools import partial
import paramiko
from cloudless.util.log import logger
from cloudless.testutils.utils import generate_unique_name
from cloudless.testutils.ssh import generate_ssh_keypair
from cloudless.types.networking import CidrBlock
from cloudless.util.exceptions import DisallowedOperationException

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
NETWORK_BLUEPRINT = os.path.join(SCRIPT_PATH, "network.yml")

class FileSystemWrapper:
    """
    This only exists to make this more testable.  A simple interface that wraps the filesystem
    operations.
    """
    def __init__(self):
        pass

    # pylint:disable=no-self-use
    def write(self, path, data, mode=None):
        """
        Writes to a file, optionally allowing setting file permissions.  Currently does not support
        append mode.
        """
        if mode:
            with open(path, "w", opener=partial(os.open, mode=mode)) as file_handle:
                file_handle.write(data)
        else:
            with open(path, "w") as file_handle:
                file_handle.write(data)

    # pylint:disable=no-self-use
    def read(self, path):
        """
        Reads a file and returns its data.
        """
        with open(path, "r") as file_handle:
            return file_handle.read()

    # pylint:disable=no-self-use
    def exists(self, path):
        """
        Checks if the given path exists.
        """
        return os.path.exists(path)

    # pylint:disable=no-self-use
    def remove(self, path):
        """
        Remove the file at the given path.
        """
        return os.remove(path)


class ImageBuilder:
    """
    Class to manage the lifecycle of building an image.  Handles the following stages:

        - Deploy: Deploys the image on the cloud provider.
        - Configure: Runs the configuration script.
        - Check: Runs the check script.
        - Save: Saves the image after it is configured and checked (must run after configure/check).
        - Cleanup: Cleans up everything that was created to build this image.
        - Build: Runs all the previous steps in order.  The only way to save an image.
    """

    def __init__(self, client, config, filesystem=FileSystemWrapper()):
        self.client = client
        self.config = config
        self.filesystem = filesystem
        self.state_path = os.path.join(self.config.get_config_dir(),
                                       "cloudless-image-build-state.json")
        self.private_key_path = os.path.join(self.config.get_config_dir(),
                                             "id_rsa_image_build")
        self.public_key_path = os.path.join(self.config.get_config_dir(),
                                            "id_rsa_image_build.pub")

    def _save_state(self, state):
        """
        Save state in a json file in our image configuration directory.
        """
        self.filesystem.write(self.state_path, json.dumps(state))

    def _save_keypair(self, keypair):
        """
        Save keys in our image configuration directory.
        """
        self.filesystem.write(self.private_key_path, keypair.private_key, mode=0o600)
        self.filesystem.write(self.public_key_path, keypair.public_key)

    def _load_state(self):
        """
        Load state from a json file in our image configuration directory.
        """
        if not self.filesystem.exists(self.state_path):
            return {}
        return json.loads(self.filesystem.read(self.state_path))

    def _remove_keypair(self):
        """
        Remove test keys from our image configuration directory.
        """
        self.filesystem.remove(self.private_key_path)
        self.filesystem.remove(self.public_key_path)

    def deploy(self):
        """
        Deploy: Deploys the image on the cloud provider.
        """
        # 1. Deploy a temporary network
        state = {}
        state["network"] = generate_unique_name("image-build")
        state["service"] = "image-build"

        # Save state first in case something fails
        if self._load_state():
            raise DisallowedOperationException(
                "Called deploy but found existing state %s in state file %s" % (
                    state,
                    self.state_path))
        self._save_state(state)
        network = self.client.network.create(state["network"], NETWORK_BLUEPRINT)

        # 2. Create temporary ssh keys
        keypair = generate_ssh_keypair()
        self._save_keypair(keypair)
        state["ssh_username"] = "cloudless_image_build"
        state["ssh_public_key"] = self.public_key_path
        state["ssh_private_key"] = self.private_key_path
        self._save_state(state)

        # 3. Deploy a service with one instance in that network
        template_vars = {
            "cloudless_image_build_ssh_key": keypair.public_key,
            "cloudless_image_build_ssh_username": state["ssh_username"]
        }
        service = self.client.service.create(network, state["service"],
                                             self.config.get_blueprint_path(),
                                             template_vars=template_vars,
                                             count=1)

        # 4. Allow port 22 to that instance
        internet = CidrBlock("0.0.0.0/0")
        self.client.paths.add(internet, service, 22)

        return service, state

    def configure(self):
        """
        Configure: Runs the configuration script.
        """
        # 1. Load existing configuration
        state = self._load_state()
        if not self._load_state():
            raise DisallowedOperationException(
                "Called configure but found no state at %s.  Call deploy first." % (
                    self.state_path))
        logger.debug("Loaded state: %s", state)

        network = self.client.network.get(state["network"])
        if not network:
            raise DisallowedOperationException("Network %s not found!" % state["network"])
        service = self.client.service.get(network, state["service"])
        if not service:
            raise DisallowedOperationException("Service %s not found!" % state["service"])
        instances = self.client.service.get_instances(service)
        if not instances:
            raise DisallowedOperationException("No running instances in service %s!" %
                                               (state["service"]))
        if len(instances) > 1:
            raise DisallowedOperationException("More than one running instance in service %s!" %
                                               (state["service"]))
        public_ip = instances[0].public_ip
        # 2. Run ./configure <ssh_user> <ssh_key_path>
        return subprocess.run([self.config.get_configure_script_path(), state["ssh_username"],
                               public_ip, self.private_key_path], check=True)

    def check(self):
        """
        Check: Runs the check script.
        """
        # 1. Load existing configuration
        state = self._load_state()
        if not self._load_state():
            raise DisallowedOperationException(
                "Called check but found no state at %s.  Call deploy first." % (
                    self.state_path))
        logger.debug("Loaded state: %s", state)

        network = self.client.network.get(state["network"])
        if not network:
            raise DisallowedOperationException("Network %s not found!" % state["network"])
        service = self.client.service.get(network, state["service"])
        if not service:
            raise DisallowedOperationException("Service %s not found!" % state["service"])
        instances = self.client.service.get_instances(service)
        if not instances:
            raise DisallowedOperationException("No running instances in service %s!" %
                                               (state["service"]))
        if len(instances) > 1:
            raise DisallowedOperationException("More than one running instance in service %s!" %
                                               (state["service"]))
        public_ip = instances[0].public_ip
        # 2. Run ./check <ssh_user> <ssh_key_path>
        return subprocess.run([self.config.get_check_script_path(), state["ssh_username"],
                               public_ip, self.private_key_path], check=True)

    def _save(self, mock=False):
        """
        Save: Saves the image after it is configured and checked (must run after configure/check)

        This is internal and not exposed on the command line because you should only save an image
        as part of a full build.  All the other steps here are for debugging and development.
        """
        # 1. Load existing configuration
        state = self._load_state()
        if not self._load_state():
            raise DisallowedOperationException(
                "Called save but found no state at %s.  Call deploy first." % (
                    self.state_path))
        logger.debug("Loaded state: %s", state)

        network = self.client.network.get(state["network"])
        if not network:
            raise DisallowedOperationException("Network %s not found!" % state["network"])
        service = self.client.service.get(network, state["service"])
        if not service:
            raise DisallowedOperationException("Service %s not found!" % state["service"])
        instances = self.client.service.get_instances(service)
        if not instances:
            raise DisallowedOperationException("No running instances in service %s!" %
                                               (state["service"]))
        if len(instances) > 1:
            raise DisallowedOperationException("More than one running instance in service %s!" %
                                               (state["service"]))
        public_ip = instances[0].public_ip

        # 2. Remove test keys
        if not mock:
            ssh = paramiko.SSHClient()
            ssh_key = paramiko.RSAKey(file_obj=open(state["ssh_private_key"]))
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=public_ip, username=state["ssh_username"], pkey=ssh_key)

            # This removes all permissions from the temporary user's home directory and sets the
            # account to expire immediately.  We unfortunately can't completely delete this
            # temporary account because we are currently logged in.
            def try_run(client, cmd):
                logger.info("running '%s'", cmd)
                _, stdout, stderr = client.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                if exit_status:
                    raise Exception("Failed to delete image build user on image: %s.  "
                                    "Exit code: %s." % (stderr.read(), exit_status))
                logger.debug("Stdout: %s", stdout.read())
            try_run(ssh, 'cd /tmp')
            try_run(ssh, 'sudo chmod -R 000 /home/%s/' % state["ssh_username"])
            try_run(ssh, 'sudo usermod --expiredate 1 %s' % state["ssh_username"])
            logger.info("Deleted test user: %s", state["ssh_username"])
            ssh.close()

        # 3. Save the image with the correct name
        logger.debug("Saving service %s with name: %s", service.name, self.config.get_image_name())
        image = self.client.image.create(self.config.get_image_name(), service)
        logger.info("Image saved with name: %s", self.config.get_image_name())

        return image

    def cleanup(self):
        """
        Cleanup: Cleans up everything that was created to build this image.
        """
        # 1. Load existing configuration
        state = self._load_state()
        if not self._load_state():
            return True

        # 2. Tear everything down
        all_services = self.client.service.list()
        for service in all_services:
            if service.network.name == state["network"]:
                self.client.service.destroy(service)
        network = self.client.network.get(state["network"])
        if network:
            self.client.network.destroy(network)
        self._save_state({})
        self._remove_keypair()
        return True

    def run(self, mock=False):
        """
        Build: Runs all the previous steps in order.  The only way to save an image.
        """
        # 1. Run all steps in order
        self.deploy()
        self.configure()
        self.check()
        self._save(mock)
        self.cleanup()

        # 2. Profit!
        return self.config.get_image_name()
