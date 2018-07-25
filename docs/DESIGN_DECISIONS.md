## VPC Address Allocation

Originally, I had VPC allocation query a sort of inventory object that queried
AWS for the current VPCs.  It did this because I wanted to not overlap existing
VPCs by default in case the user wanted to peer them or something.  I think
this was a mistake, and this is a design choice to change that.

When I allocate a VPC, I want to control the range in which the VPC is
allocated.  So what I really want is:

- The subnet size
- A list of acceptable ranges
- A list of excluded ranges

The VPC allocation shouldn't do anything clever to find these ranges, because
that bakes in more stuff that the library has to maintain.  Keeping these as
inputs to the creation keeps it more generic and allows anything to be plugged
in.

The default behavior will be to use "10.0.0.0/8" with size of "16".  Someday
the size should probably be the number of servers, but this is easier for now
and I can change it because this is just a prototype.  I don't know how this
will work with IPV6 yet.

Having a default where VPCs overlap I think is okay, since the entire premise
of this tool is that entire VPCs should be disposable, and if you're spinning
up multiple VPCs you should already have the capability to create and destroy
them quickly and reproducibly.  So if a user makes the mistake of not passing
the exclude ranges the consequences should not be large.

## Datacenter (VPC) and Network/Service Interface

Since the Network/Service must be provisioned in a VPC, there's a question of
how that layer interacts with the VPC layer.

To keep it loosely coupled, both layers must be usable without the other.  The
network layer must be usable without the VPC layer and the VPC layer must be
usable without the network layer.

Since not all clouds support labels (unfortunately), the only cloud agnostic
way is to actually require passing the ID of the VPC, so that's the way the
network will know what VPC to provision in until that changes.

Also, the network will not automatically create the VPC.

## Coupling between Network and Service Layers

In general, things should be usable on their own, but the exception here is the
network and service layers.

There are a few reasons for this.  First, the routing and path setup would need
to be done twice if the user had to create a network and pass it into the
service layer as opposed to the service layer knowing how to create its own
network.  Second, the service layer needs to control the network layer in order
to expand its cross availability zone redundancy.  Finally, there is no reason
that I can think of for a user to need multiple services for a single group of
subnets.  Any necessary coupling can be acheived by creating two groups of
subnets and adding paths between them, which also creates a situation where
things are easier to independently upgrade.

For that reason, I'm actually going to treat the Network and the Service as the
same level of abstration from the user perspective, with the small detail that
the Service will use the Network layer internally to provision its network.  In
that way the Network becomes the "custom service" use case when you want to
provision subnets but then use raw AWS or another tool.

## (Tentative) Top Level Wrapper

One feature request from the first user test was to be able to list all
resources at once to figure out what's going on.

Given that I want to keep things loosely coupled, this may be solveable by
having a thin glue layer pull together all the independent libraries and run
them to aggregate the complete view.  The advantage is that it gives a nice
quickstart experience while the independent libraries give the more fine
grained control.  The downside is that it's a bit ugly and there may be a
better or more elegant way to do it.  I also don't really know what to do about
all of Amazon's other random features if I provide that, so really having each
piece focus on a self contained thing is actually nice (so then what to do
about VPC dependency violations?  Just friendlier error messaging after trying
to discover things that might be blocking deletion?).

## (Tentative) Declarative Configuration, Dynamic Resources

This seems like a clear one in retrospect.  Declarative configuration has a
purpose, in defining what something is.  While this is meant to be more dynamic
than terraform in that resources are dynamic and not declarative, what those
resources are could still be declarative.  This parallels a launch configuration
in an AWS autoscaling group.
