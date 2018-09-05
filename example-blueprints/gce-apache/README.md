# Apache Example Blueprint

This is a blueprint that creates a service running Apache.

Since the image name in the blueprint is an GCE image, this only runs on GCE.

## Run Tests

```
pipenv update
pipenv run cloudless-test --provider gce run
```
