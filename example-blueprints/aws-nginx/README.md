# Nginx Example Blueprint

This is a blueprint that creates a service running Nginx.

Since the image name in the blueprint is an AWS image, this only runs on AWS.

## Run Tests

```
pipenv update
pipenv run cloudless-test --provider aws run
```
