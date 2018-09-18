# Cloudless

Cloudless makes it easier to interact with cloud resources by doing most of the
work that a human doesn't need to care about for you, and by being transparent
about what it's doing.

- [Homepage](https://getcloudless.com)
- [Documentation](https://docs.getcloudless.com)
- [Github](https://github.com/getcloudless/cloudless)

## Installation

This project depends on [Python
3.6.0](https://www.python.org/downloads/release/python-360/) or greater.  To
install, run:

```shell
pip3 install cloudless
```

## Quick Start

These examples show how to quickly create a simple service that is accessible on
port 80 in Google Compute Engine and in Amazon Web Services.  Run any command
with `--help` for more usage.

### Google Compute Engine

To set up the Google Compute Engine client, you must first create your Google
Compute Engine account and navigate to
[https://console.cloud.google.com/iam-admin/serviceaccounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
There you can select your project and create a service account.  Remember the
service account email and create a key for this service account.  Download and
save this key on your local machine, remembering the path.

You will also need the project ID (not the project name).  Go to
[https://console.cloud.google.com/iam-admin/settings/project](https://console.cloud.google.com/iam-admin/settings/project)
and select your project to find your project ID.

```
cldls init --provider gce
cldls network create example-blueprints/network/blueprint.yml
cldls service create mynet myservice example-blueprints/gce-apache/blueprint.yml
cldls paths allow_external mynet myservice 0.0.0.0/0 80
cldls service get mynet myservice
# Navigate to the "public_ip" of each instance in a browser to see the service.
```

### Amazon Web Services

To set up the Amazon Web Services client, follow the steps at
[https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
to configure the aws cli.  Currently, cloudless only uses the "default" aws
profile that is configured in this way.  After you set up a default profile that
works with the AWS cli, everything in cloudless should work.

```
cldls init --provider aws
cldls network create mynet example-blueprints/network/blueprint.yml
cldls service create mynet myservice example-blueprints/aws-nginx/blueprint.yml
cldls paths allow_external mynet myservice 0.0.0.0/0 80
cldls service get mynet myservice
# Navigate to the "public_ip" of each instance in a browser to see the service.
```

## Client Setup In Python API

In the Python API, you must create a client object to connect to the cloud
platform that you'll be working with.  The client handles authentication with
the cloud provider, so you must pass it the name of the provider and the
authentication credentials.

If you are trying this project for the first time, it's recommended that you use
the "mock-aws" client.

### Google Compute Engine Client

To use the Google Compute Engine client, you must create a service account and
download the credentials locally.  Because this provider is implemented using
[Apache Libcloud](https://libcloud.apache.org/), you can refer to the [Google
Compute Engine Driver
Setup](https://libcloud.readthedocs.io/en/latest/compute/drivers/gce.html#getting-driver-with-service-account-authentication)
documentation in that project for more details.

When you have the credentials, you can do something like this, preferably in a
dotfile you don't commit to version control.  Note the credentials file is in
JSON format:

```shell
export CLOUDLESS_GCE_USER_ID="sverch-cloudless@cloudless-000000.iam.gserviceaccount.com"
export CLOUDLESS_GCE_CREDENTIALS_PATH="/home/sverch/.gce/credentials.json"
export CLOUDLESS_GCE_PROJECT_NAME="cloudless-000000"
```

Then, you can run these commands in a python shell to create a GCE client:

```python
import cloudless
import os
client = cloudless.Client("gce", credentials={
    "user_id": os.environ['CLOUDLESS_GCE_USER_ID'],
    "key": os.environ['CLOUDLESS_GCE_CREDENTIALS_PATH'],
    "project": os.environ['CLOUDLESS_GCE_PROJECT_NAME']})
```

### Amazon Web Services Client

Currently no credentials can be passed in as arguments for the AWS provider
(they are ignored).  However this provider is implemented with
[Boto](http://docs.pythonboto.org/en/latest/), which looks in many other places
for the credentials, so you can configure them in other ways.  See the [boto3
credential setup
documentation](https://boto3.readthedocs.io/en/latest/guide/configuration.html)
for more details.

Once you have set up your credentials, you can run the following to create an
AWS client:

```python
import cloudless
client = cloudless.Client("aws", credentials={})
```

### Mock Amazon Web Services Client

The Mock AWS client is for demonstration and testing.  Since it is all running
locally, you don't need any credentials.  Simply run:

```python
import cloudless
client = cloudless.Client("mock-aws", credentials={})
```

## Architecture

There are only three objects in Cloudless: A Network, a Service, and a Path.  This
is an example that shows a Network `dev`, a `public_load_balancer` Service, an
`internal_service` Service, a Path from the internet to `public_load_balancer`
on port 443, and a Path from `public_load_balancer` to `internal_service` on
port 80.  See the [visualization](#visualization) section for how to generate
this graph.

![Cloudless Simple Service Example](docs/images/example.svg)

### Network

A Network is the top level container for everything else.  To create a new
network, run:

```python
dev_network = client.network.create("dev")
```

This will return the "Network" object that describes the network that was
created.  You can retrieve an existing network or list all existing networks by
running:

```python
dev_network = client.network.get("dev")
all_networks = client.network.list()
```

Finally, to destroy a network:

```python
client.network.destroy(dev_network)
```

Create should use sane defaults, but if you need to do something special see
[docs/network-configuration.md](docs/network-configuration.md).

In [ipython](https://ipython.org/), you can run `<object>?` to [get help on any
object](https://ipython.readthedocs.io/en/stable/interactive/python-ipython-diff.html#accessing-help),
for example `client.network.create?`.

### Service

A Service a logical group of instances and whatever resources are needed to
support them (subnetworks, firewalls, etc.).

To create a Service, you must first define a configuration file called a
"blueprint" that specifies how the service should be configured.  This is an
example of what a Service blueprint might look like:

```yaml
---
network:
  subnetwork_max_instance_count: 768

placement:
  availability_zones: 3

instance:
  public_ip: True
  memory: 4GB
  cpus: 1
  gpu: false
  disks:
    - size: 8GB
      type: standard
      device_name: /dev/sda1

image:
  name: "ubuntu/images/hvm-ssd/ubuntu-xenial-16.04-amd64-server-*"

initialization:
  - path: "haproxy-cloud-config.yml"
    vars:
      PrivateIps:
        required: true
```

The "network" section tells Cloudless to create subnetworks for this service big
enough for 768 instances.

The "placement" section tells Cloudless to ensure instances in this service are
provisioned across three availaibility zones (which most cloud providers
guarantee are meaningfully isolated from each other for resilience).

The "instance" section describes the resource reqirements of each instance.
Cloudless will automatically choose a instance type that meets these requirements.

The "image" section represents the name of the image you want your instances to
have.  In this case, we are using an image name only found in AWS by default, so
this example will only work there.  See `example-blueprints/gce-apache` for a
GCE example blueprint.

The "initialization" section describes startup scripts that you want to run when
the instance boots.  You may also pass in variables, which will get passed to
the given file as [jinja2](http://jinja.pocoo.org/) template arguments.  This is
a good place to specify environment specific configuration, so your base image
can stay the same across environments.

Once you have the blueprint, the example below shows how you could use it.
These examples create a group of private instances and then create some HAProxy
instances in front of those instances to balance load.  Note that many commands
take `dev_network` as the first argument.  That's the same network object
returned by the network commands shown above.

```python
internal_service = client.service.create(dev_network, "private",
                                         blueprint="example-blueprints/aws-nginx/blueprint.yml")
private_ips = [instance.private_ip for instance in client.service.get_instances(internal_service)]
load_balancer_service = client.service.create(dev_network, "public",
                                              blueprint="example-blueprints/aws-haproxy/blueprint.yml",
                                              template_vars={"PrivateIps": private_ips})
internal_service = client.service.get(dev_network, "public")
load_balancer_service client.service.get(dev_network, "private")
client.service.list()
client.service.destroy(internal_service)
client.service.destroy(load_balancer_service)
```

There is another example blueprint that works with GCE if you created the GCE
client above:

```python
client.instances.create(dev_nework, "public", blueprint="example-blueprints/gce-apache/blueprint.yml")
```

### Path

The Path is how you tell Cloudless that two services should be able to communicate.
No blueprint is needed for this, but you need to have the service objects you
created earlier.  This example adds a path from the load balancer to the
internal service on port 80 and makes the load balancer internet accessible on
port 443:

```python
from cloudless.types.networking import CidrBlock
internet = CidrBlock("0.0.0.0/0")
client.paths.add(load_balancer_service, internal_service, 80)
client.paths.add(internet, load_balancer_service, 443)
```

You can check whether things have access to other things or print out all paths
with the following functions:

```python
client.paths.has_access(load_balancer_service, internal_service, 80)
client.paths.internet_accessible(load_balancer_service, 443)
client.paths.internet_accessible(internal_service, 443)
client.paths.list()
print(client.graph())
```

## Visualization

Get a summary in the form of a graphviz compatible dot file by running:

```python
client.graph()
```

To generate the vizualizations, run:

```shell
cd ui && env PROVIDER=<provider> bash graph.sh
```

And open `ui/graph.html` in a browser.  Note this won't work for the `mock-aws`
provider since it will be running in a different process.

## Blueprint Tester

This project also provides a framework to help test that blueprint files work as
expected.  The framework will create, verify, and clean up the service under
test.  It also spins up all dependent services so you can test services "in
context".  It's sort of a hybrid between a unit test and an integration test.

These examples assume you are using a profile called "gce" that is configured
with the `gce` provider, but there are other example blueprints in
[`example-blueprints`](example-blueprints) that you can use AWS to test.  They
are currently different because the different cloud providers provide different
base images.

First, to create the service:

```shell
$ cldls --profile gce blueprint create example-blueprints/gce-apache/blueprint-test-configuration.yml
Creation complete!
To log in, run:
ssh -i example-blueprints/gce-apache/id_rsa_test cloudless@35.237.12.140
$ ssh -i example-blueprints/gce-apache/id_rsa_test cloudless@35.237.12.140
...
...

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

cloudless@test-network-jmeiwknbsg-test-service-hswonxmeda-0:~$ 
```

This will create a temporary network to sandbox the test.  Now, to verify that
the service is behaving as expected:

```shell
$ cldls --profile gce blueprint verify example-blueprints/gce-apache/blueprint-test-configuration.yml
INFO:cloudless.providers.gce:Discovering subnetwork test-network-jmeiwknbsg, test-service-hswonxmeda
INFO:cloudless.util:Attempt number: 1
INFO:cloudless.util:Verify successful!
Verify complete!
To log in, run:
ssh -i example-blueprints/gce-apache/id_rsa_test cloudless@35.237.12.140
```

Finally, to clean up everything:

```shell
$ cldls --profile gce blueprint cleanup example-blueprints/gce-apache/blueprint-test-configuration.yml
```

If you want to run all the previous steps all together, you can run:

```shell
$ cldls --profile gce blueprint test example-blueprints/gce-apache/blueprint-test-configuration.yml
```

See [example-blueprints](example-blueprints) for examples of how to set up a
blueprint to be testable with this framework.

## Testing

To run the local tests run:

```shell
pipenv install --dev
tox
```

To run tests against GCE and AWS, run:

```shell
tox -e gce
tox -e aws
```

For GCE, you must set `CLOUDLESS_GCE_USER_ID`, `CLOUDLESS_GCE_CREDENTIALS_PATH`, and
`CLOUDLESS_GCE_PROJECT_NAME` as described above.
