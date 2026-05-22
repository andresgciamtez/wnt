"""Translation helpers for Water Network Tools."""

from qgis.PyQt.QtCore import QCoreApplication

TR_CONTEXT = 'WaterNetworkTools'


def tr(message):
    """Translate plugin text using the shared Water Network Tools context."""
    return QCoreApplication.translate(TR_CONTEXT, message)
