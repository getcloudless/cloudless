#!/usr/bin/env python


class BadEnvironmentStateException(Exception):
    """
    Throw this when the cloud environment you're deploying to is not in the
    state it should be (violates some invariant).
    """
    pass


class DisallowedOperationException(Exception):
    pass


class NotEnoughIPSpaceException(Exception):
    pass


class OperationTimedOut(Exception):
    pass
