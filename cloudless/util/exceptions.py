"""
General Cloudless exeptions.
"""


class BadEnvironmentStateException(Exception):
    """
    Throw this when the cloud environment you're deploying to is not in the
    state it should be (violates some invariant).
    """


class DisallowedOperationException(Exception):
    """
    Trying to do something that's invalid.
    """


class ProfileNotFoundException(Exception):
    """
    Could not find the provided profile.
    """


class NotEnoughIPSpaceException(Exception):
    """
    Could not allocate the given CIDR range.
    """


class OperationTimedOut(Exception):
    """
    Exceeded max retries to perform operation.
    """


class BlueprintException(Exception):
    """
    Encountered error interpreting Blueprint file.
    """


class BadConfigurationException(Exception):
    """
    Encountered error interpreting Configuration file.
    """


class IncompleteOperationException(Exception):
    """
    This is if we are still waiting for something to happen, normally should retry.
    """
