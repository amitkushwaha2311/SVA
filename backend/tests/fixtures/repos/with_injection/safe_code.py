"""Normal source code in injection fixture — should not trigger findings."""


def safe_function() -> str:
    """This file has no injection patterns."""
    return "safe"
