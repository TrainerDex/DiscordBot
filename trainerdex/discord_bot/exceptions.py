from discord import ClientException


class ModuleHealthCheckException(ClientException):
    """Raises when a health check on a module fails."""

    pass
