"""Import smoke tests for the restructured plugin package."""

import pytest

pytest.importorskip("qgis")


pytestmark = pytest.mark.qgis


def test_restructured_plugin_imports():
    """Core plugin modules import from their new packages."""
    from wnt.processes.wnt_network_to_graph import NetworkToGraphAlgorithm
    from wnt.utils.utils_core import WntNetwork
    from wnt.utils.utils_epanet_api import EpanetToolkit
    from wnt.utils.utils_graph import Graph
    from wnt.wnt_provider import WaterNetworkToolsProvider

    assert NetworkToGraphAlgorithm
    assert WntNetwork
    assert EpanetToolkit
    assert Graph
    assert WaterNetworkToolsProvider

