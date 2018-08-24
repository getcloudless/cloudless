# Network Configuration

A network can be configured by passing a "blueprint" argument to the create
command.  A Blueprint file for a network with the defaults set might look like:

```yaml
---
network:
  legacy_network_size_bits: 16
  allowed_private_cidr: "10.0.0.0/8"
```

The `legacy_network_size_bits` option only matters for the AWS provider, since
GCE lets you creates subnets directly without a top level network, but AWS does
not.  That option tells AWS to create a top level network (VPC) of size 16,
which will mean that the network has 2^16 unique IP addresses in it.  Note that
everything is currently still using IPv4.

The `allowed_private_cidr` is useful if you might peer networks and don't want
the private ranges to overlap.  For AWS you must set this on the network
creation call, but since GCE doesn't allocate any networks until subnetworks are
created you must set this block in the service blueprint for GCE to honor your
allowed ranges.
