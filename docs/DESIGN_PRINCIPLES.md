## Design Principles

### All Dynamic

The source of truth should be the cloud, or some kind of inventory.  You should
not ever have any static declarations of what your infrastructure looks like.
In fact, that should be impossible without extra work.

### User Friendly

Try to be like the person who wrote the requests library for python and pyenv.
Make this library "for humans".

### Correct Abstractions

Think very carefully about the abstractions, and make sure that we're using the
correct one.  Is a container the right abstraction?  What about a server?  How
do we want to express networking rules?

### Make It Hard To Do The Wrong Thing

I'm sick of arguing with people that single points of failure are bad.  This
tool should explicitly not support antipatterns.

### Teach The Why

A corollary to being strict and preventing bad behaviour means that the tool
has to help explain why the behaviour is bad.  If something isn't allowed but
the error message is too generic for people to understand why, that's a bug.

### People Are Lazy

No one will take the time to understand what's actually going on.  Just make the
thing do what it should.

### Unix Philosopy

Each component should be useful on its own without using any of the other
components.
