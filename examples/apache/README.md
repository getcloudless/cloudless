# Apache Service Example

This is an example of creating a service running Apache.  Note that this
blueprint references an image created by the base image scripts at
[../base-image/README.md](../base-image/README.md), so this will fail unless you
run that first.

## Usage

The file at `blueprint.yml` can be used in any service command:

```
cldls service create blueprint.yml
```

You can run the service's regression tests with:

```
cldls service-test run service_test_configuration.yml
```

Note that these are completely independent of what provider you're using,
assuming you've already built the [Base Image](../base-image/README.md).

## Workflow

The main value of the test framework is that it is focused on the workflow of
actually developing a service.  For example, if you want to deploy a service
(and all its dependencies) that you can work on without running the full test,
you can run:

```
cldls service-test deploy service_test_configuration.yml
```

This command saves the SSH keys locally and will display the SSH command that
you need to run to log into the instance.

Now, say you want to actually check that the service is behaving as expected:

```
cldls service-test check service_test_configuration.yml
```

You can run this as many times as you want until it's working, as you are logged
in.  Finally, clean everything up with:

```
cldls service-test cleanup service_test_configuration.yml
```

You're done!  The run step will run all these steps in order.

## Files

- `service_test_configuration.yml`: Configuration file for the service test
  framework.
- `blueprint.yml`: Blueprint that is actually used to create the service.  This
  is the thing we are really testing.
- `apache_startup_script.sh`: Script referenced by the blueprint that will set
  up Apache.
- `blueprint_fixture.py`: Python test fixture that will set up dependencies and
  verify that things are behaving as expected.
