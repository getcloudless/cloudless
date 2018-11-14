# Cloudless Contributor's Guide

Welcome to Cloudless!  Thank you for considering contributing to this project.

If you are new to this project, see the [project README](README.md), the
[project homepage](https://getcloudless.com), and the [project
documentation](https://docs.getcloudless.com) to get an idea of what Cloudless
is about.

## How To Contribute

There are two parts of this project where contributions are welcome:

- Cloudless Core
- Cloudless Modules

The Cloudless Core is all the code in this project.  To contribute to the core,
choose an [existing issue](https://github.com/getcloudless/cloudless/issues) or
create a new one that describes the problem you want to solve, fork this
repository, and then create a pull request on this repo referencing the issue.

The Cloudles Modules are sets of integration tests and configuration that
creates specific services.  You can see some examples in the [getcloudless
github organization](https://github.com/getcloudless).  To contribute a module,
for now fork this repo and create a pull request that adds your module to the
[module listing](MODULES.md).

## How To Test

If you create a PR with a change, we can help with testing, but if you want to
test you should use `tox` to run the local tests, and `tox -e aws` and `tox -e
gce` for the tests against the real cloud providers.  See the [project
README](README.md#testing) for how to properly configure the credentials for
those tests.
