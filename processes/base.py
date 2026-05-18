"""Base classes for Water Network Tools processing algorithms."""

from qgis.core import QgsProcessingAlgorithm

from ..i18n import tr


class WntProcessingAlgorithm(QgsProcessingAlgorithm):
    """Processing algorithm base class with a shared translation context."""

    def tr(self, message):
        """Return a translated string."""
        return tr(message)
