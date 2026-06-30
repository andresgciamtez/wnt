"""Lazy safe XML parsing helpers."""


def parse(source):
    """Parse XML with defusedxml, failing clearly if it is unavailable."""
    try:
        from defusedxml import ElementTree as safe_et
    except ImportError as exc:
        raise RuntimeError(
            "defusedxml is required to parse external XML safely. "
            "Install defusedxml in the QGIS Python environment."
        ) from exc
    return safe_et.parse(source)
