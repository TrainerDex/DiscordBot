import re


def validate_trainer_nickname(nickname: str) -> bool:
    """Validate a trainer nickname."""
    return bool(re.match(r"^[A-Za-z0-9]{3,15}$", nickname))
