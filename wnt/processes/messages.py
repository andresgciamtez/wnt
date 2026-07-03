"""Consistent Processing feedback messages."""

from qgis.core import QgsProcessingException

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
    push_warning = getattr(feedback, "pushWarning", None)
    if push_warning is not None:
        push_warning(text)
    else:
        feedback.pushInfo(f"WARNING: {text}")


def error(feedback, text):
    """Report a fatal Processing error and stop algorithm execution."""
    message = f"ERROR: {text}"
    try:
        feedback.reportError(message, fatalError=True)
    except TypeError:
        feedback.reportError(message)
    raise QgsProcessingException(message)

