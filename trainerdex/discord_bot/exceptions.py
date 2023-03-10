from discord import ClientException


class CogHealthCheckException(ClientException):
    """Raises when a health check on a cog fails."""

    pass
