# Base Image Build Example

This is an example of building a base image across multiple cloud providers.

## Usage

Because we are starting from stock Ubuntu images, and because the images
provided by the different cloud providers have different names, we have to have
different build configurations.  If you were building on an image that you had
created, or if you copied the stock configuration to the same name on both
providers, you could have one configuration for both.

Assuming you've configured the `aws` profile to use the `aws` provider, with the
`cldls` command, run:

```
cldls --profile aws image-build run aws_image_build_configuration.yml 
```

Assuming you've configured the `gce` profile to use the `gce` provider, with the
`cldls` command, run:

```
cldls --profile gce image-build run gce_image_build_configuration.yml 
```

## Workflow

The main value of this framework is that it is focused on the workflow of
actually developing an image.  For example, if you want to deploy an instance
that you can work on without running the full build, you can run:

```
cldls --profile gce image-build deploy gce_image_build_configuration.yml 
```

This command saves the SSH keys locally and will display the SSH command that
you need to run to log into the instance.

Now, say you want to actually test that the configuration step works properly:

```
cldls --profile gce image-build configure gce_image_build_configuration.yml 
```

You can run this as many times as you want until it's working.  Finally, you can
run your tests to check that the configuration behaves as expected:

```
cldls --profile gce image-build check gce_image_build_configuration.yml 
```

You're done!  Clean everything up with:

```
cldls --profile gce image-build cleanup gce_image_build_configuration.yml 
```

You're done!  When you're ready to actually save an image, you can run the full
build.  Cloudless does not support saving an image without the full build so
that there is some confidence that the image is in a predictable and
reproducible state.

## Files

- `aws_blueprint.yml`: Blueprint for AWS.  Used to create the service with a
  single instance.
- `gce_blueprint.yml`: Blueprint for GCE.  Used to create the service with a
  single instance.
- `aws_image_build_configuration.yml`: Build configuration for AWS.  The only
  difference is that it references a different blueprint.
- `gce_image_build_configuration.yml`: Build configuration for GCE.  The only
  difference is that it references a different blueprint.
- `image_build_allow_ssh.sh`: Required startup script that sets up the build
  user.  This is what allows SSH logins for the `configure` and `check` scripts.
- `configure`: Shell script that is called by cloudless with the arguments
  `<ssh_username>`, `<instance_public_ip>`, and `<ssh_private_key_path>` in that
  order.  You can use this to configure an instance.
- `check`: Shell script that is called by cloudless with the arguments
  `<ssh_username>`, `<instance_public_ip>`, and `<ssh_private_key_path>` in that
  order.  You can use this to check that an instance was configured as expected.
