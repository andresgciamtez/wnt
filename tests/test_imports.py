"""Import smoke tests for the restructured plugin package."""

import pytest


pytestmark = pytest.mark.qgis


def test_restructured_plugin_imports():
    """Core plugin modules import from their new packages."""
    from wnt.processes.wnt_graph_from_network import GraphFromNetworkAlgorithm
    from wnt.utils.utils_core import WntNetwork
    from wnt.utils.utils_epanet_api import EpanetToolkit
    from wnt.utils.utils_graph import Graph
    from wnt.wnt_provider import WaterNetworkToolsProvider

    assert GraphFromNetworkAlgorithm
    assert WntNetwork
    assert EpanetToolkit
    assert Graph
    assert WaterNetworkToolsProvider

