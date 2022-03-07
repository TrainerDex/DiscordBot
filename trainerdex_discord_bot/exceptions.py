from discord import ClientException


class CogHealthcheckException(ClientException):
    """Raises when a Healthcheck on a cog fails."""

    pass
