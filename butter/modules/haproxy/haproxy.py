# pylint: disable=missing-docstring
import os

import logging

# pylint: disable=invalid-name
logger = logging.getLogger(__name__)

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
HAPROXY_SRC = "%s/haproxy-cloud-config.yml" % SCRIPT_PATH
HAPROXY_DST = "%s/haproxy-cloud-config-generated.yml" % SCRIPT_PATH
HAPROXY_SERVICE = "%s/haproxy-service.yml" % SCRIPT_PATH


def create(client, network, name, destination_name):
    with open(HAPROXY_SRC) as source:
        startup_script_contents = source.read()
        instances = client.instances.discover(network, destination_name)
        private_ips = [i["PrivateIp"] for i in instances["Instances"]]
        for i in [0, 1, 2]:
            startup_script_contents = startup_script_contents.replace(
                "HOST_%s_PLACEHOLDER" % i, private_ips[i])
        with open(HAPROXY_DST, "w") as dest:
            dest.truncate()
            dest.write(startup_script_contents)
        logger.info('Found instances: %s for %s', private_ips,
                    destination_name)
    instances = client.instances.create(network, name, blueprint=HAPROXY_SERVICE)
    add_path = client.paths.add(network, name, destination_name, 80)
    expose = client.paths.expose(network, name, 80)
    return {"Instances": [instances], "AddPath": [add_path], "Expose":
            [expose]}


def destroy(client, network, name, destination_name):
    client.paths.remove(network, name, destination_name, 80)
    return client.instances.destroy(network, name)


def discover(client, network, name):
    return client.instances.discover(network, name)
