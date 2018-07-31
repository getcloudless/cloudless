# Butter

:warning: :construction: :skull: This is a proof of concept, do not use in
production. :skull: :construction: :warning:

An experimental tool that should abstract away some of the things that a person
shouldn't have to worry about.  By doing that, it should also make it easier to
build portable infrastructure across different cloud platforms as a side effect.

## Installation

```
pipenv install <path>/<to>/butter
```

## Usage

### Google Compute Engine Client

```
import butter
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
client.network.create("dev", blueprint="tests/blueprints/network.yml")
client.network.discover("dev")
client.network.list()
client.network.destroy("dev")
```

### Subnetwork (Subnets)

```
client.subnetwork.create("dev", "public", blueprint="tests/blueprints/subnetwork.yml")
client.subnetwork.discover("dev", "public")
client.subnetwork.list()
client.subnetwork.destroy("dev", "public")
```

### Instances (VMs)

```
client.instances.create("dev", "public", blueprint="tests/blueprints/service.yml")
client.instances.create("dev", "private", blueprint="tests/blueprints/service.yml")
client.instances.discover("dev", "public")
client.instances.discover("dev", "private")
client.instances.list()
client.instances.destroy("dev", "public")
client.instances.destroy("dev", "private")
```

### Paths (Firewalls)

```
client.paths.expose("dev", "public", 80)
client.paths.add("dev", "public", "private", 80)
client.paths.list()
client.paths.graph()
```

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

## Module Testing

This project provides a framework to test "modules" or "blueprints".  See
[example-modules/README.md](example-modules/README.md) for details.
