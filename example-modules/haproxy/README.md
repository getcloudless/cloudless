# HAProxy example module

This is a blueprint that creates an instance running HAProxy and takes the IP
addresses of the servers behind the load balancer as blueprint template
arguments.

This is just an example, in reality you'd want to use a load balancer
configuration that was more dynamic and took something like the service name
instead of the IP addresses.

## Run Tests

```
pipenv update
pipenv run python runner.py
```
