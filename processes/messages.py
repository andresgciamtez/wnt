"""Consistent Processing feedback messages."""

SEPARATOR = "-" * 48


def start(feedback, title):
    """Write a standard process header."""
    feedback.pushInfo(SEPARATOR)
    feedback.pushInfo(f"Process: {title}")


def finish(feedback):
    """Write a standard process footer."""
    feedback.pushInfo("Status: completed")
    feedback.pushInfo(SEPARATOR)


def info(feedback, label, value):
    """Write a labelled value."""
    feedback.pushInfo(f"{label}: {value}")


def message(feedback, text):
    """Write an informational message."""
    feedback.pushInfo(text)


def crs(feedback, crs_):
    """Write CRS information."""
    authid = crs_.authid() if hasattr(crs_, "authid") else str(crs_)
    if authid:
        info(feedback, "CRS", authid)
    else:
        warning(feedback, "CRS is not set")


def warning(feedback, text):
    """Write a warning message."""
    feedback.pushInfo(f"WARNING: {text}")


def error(feedback, text):
    """Write an error message."""
    feedback.reportError(f"ERROR: {text}")

