class JenticException(Exception):
    """Base exception for Jentic."""

    pass


class JenticEnvironmentError(JenticException):
    """Exception raised for errors related to environment."""

    pass


class MissingAgentKeyError(JenticEnvironmentError):
    """Exception raised for errors related to missing agent key."""

    pass


class JenticAPIError(JenticException):
    """Exception raised for errors returned by the Jentic API."""

    pass


class JenticCredentialsError(JenticException):
    """Exception raised for errors related to credentials."""

    pass
