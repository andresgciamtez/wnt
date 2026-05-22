"""QGIS plugin entry point."""

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Return the plugin instance used by QGIS.

    :param iface: A QGIS interface instance
    :type iface: QgsInterface
    """
    from .wnt import WaterNetworkToolsPlugin
    return WaterNetworkToolsPlugin()


