"""
General Butter exeptions.
"""


class BadEnvironmentStateException(Exception):
    """
    Throw this when the cloud environment you're deploying to is not in the
    state it should be (violates some invariant).
    """
    pass


class DisallowedOperationException(Exception):
    """
    Trying to do something that's invalid.
    """
    pass


class NotEnoughIPSpaceException(Exception):
    """
    Could not allocate the given CIDR range.
    """
    pass


class OperationTimedOut(Exception):
    """
    Exceeded max retries to perform operation.
    """
    pass
