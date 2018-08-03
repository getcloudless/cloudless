# Butter

:warning: :construction: :skull: This is a proof of concept, do not use in
production. :skull: :construction: :warning:

An experimental tool that should abstract away some of the things that a person
shouldn't have to worry about.  By doing that, it should also make it easier to
build portable infrastructure across different cloud platforms as a side effect.

## Installation

```
pipenv install git+https://github.com/sverch/butter.git#egg=butter
```

## Usage

### Google Compute Engine Client

```
import butter
import os
client = butter.Client("gce", credentials={
    "user_id": os.environ['BUTTER_GCE_USER_ID'],
    "key": os.environ['BUTTER_GCE_CREDENTIALS_PATH'],
    "project": os.environ['BUTTER_GCE_PROJECT_NAME']})
```

See
https://libcloud.readthedocs.io/en/latest/compute/drivers/gce.html#getting-driver-with-service-account-authentication
for more details.

### Amazon Web Services Client

```
import butter
client = butter.Client("aws", credentials={})
```

Currently no credentials can be passed, and the client uses whatever is the
default configuration for your environment.  See
https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html.

### Network (VPC)

```
client.network.create("dev", blueprint="example-blueprints/network/blueprint.yml")
client.network.discover("dev")
client.network.list()
client.network.destroy("dev")
```

### Subnetwork (Subnets)

```
client.subnetwork.create("dev", "public", blueprint="example-blueprints/subnetwork/blueprint.yml")
client.subnetwork.discover("dev", "public")
client.subnetwork.list()
client.subnetwork.destroy("dev", "public")
```

### Instances (VMs)

The example blueprints are different for AWS and GCE because the provided OS
images are different.  If the same base image was created for both platforms
these wouldn't be different.

#### AWS Instances

```
instances = client.instances.create("dev", "private",
                                    blueprint="example-blueprints/aws-nginx/blueprint.yml")
private_ips = [i["PrivateIp"] for i in instances["Instances"]]
client.instances.create("dev", "public",
                        blueprint="example-blueprints/aws-haproxy/blueprint.yml",
                        template_vars={"PrivateIps": private_ips})
client.instances.discover("dev", "public")
client.instances.discover("dev", "private")
client.instances.list()
client.instances.destroy("dev", "public")
client.instances.destroy("dev", "private")
```

#### GCE Instances

```
client.instances.create("dev", "public", blueprint="example-blueprints/gce-apache/blueprint.yml")
client.instances.discover("dev", "public")
client.instances.list()
client.instances.destroy("dev", "public")
```

### Paths (Firewalls)

```
client.paths.expose("dev", "public", 80)
client.paths.add("dev", "public", "private", 80)
client.paths.list()
```

### Prototype UI

Get a summary in the form of a graphviz compatible dot file by running:

```
client.paths.graph()
```

To generate the vizualizations, run:

```
cd ui && env PROVIDER=<provider> bash graph.sh
```

And open `ui/graph.html` in a browser.

### Blueprint Tester

This project provides a framework to help test that blueprint files work as
expected.

Example (butter must be installed):

```
butter-test --provider aws --blueprint_dir example-blueprints/haproxy run
```

Run `butter-test` with no arguments for usage.

This runner tries to import `blueprint_fixture.BlueprintTest` from the root of
your blueprint directory.  This must be a class that inherits from
`butter.testutils.fixture.BlueprintTestInterface` and implements all the
required methods.  See the documentation on that class for usage details.

The runner expects the blueprint file that you are testing to be name
`blueprint.yml` in the blueprint directory.

See [example-blueprints](example-blueprints) for all examples.

## Testing

To run the local tests run:

```
pipenv install --dev
tox
```

To run tests against GCE and AWS, run:

```
pytest -m "gce" --fulltrace
pytest -m "aws" --fulltrace
```

For GCE, you must set `BUTTER_GCE_USER_ID`, `BUTTER_GCE_CREDENTIALS_PATH`, and
`BUTTER_GCE_PROJECT_NAME` as described above.
