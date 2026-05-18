"""Coverage for Processing algorithm metadata and parameter setup."""

import pytest

from wnt.wnt_provider import WaterNetworkToolsProvider

from .utilities import get_qgis_app


QGIS_APP = get_qgis_app()


pytestmark = pytest.mark.qgis


def test_provider_metadata_icon_and_unload():
    provider = WaterNetworkToolsProvider()

    assert provider.id() == "wnt"
    assert provider.name() == "Water Network Tools"
    assert provider.longName() == "Water Network Tools"
    assert provider.icon() is not None
    assert provider.unload() is None


def test_all_algorithms_expose_metadata_and_parameters():
    provider = WaterNetworkToolsProvider()
    provider.loadAlgorithms()

    assert len(provider.algorithms()) == 21

    for algorithm in provider.algorithms():
        clone = algorithm.createInstance()

        assert type(clone) is type(algorithm)
        assert algorithm.name()
        assert algorithm.displayName()
        assert algorithm.group()
        assert algorithm.groupId()
        assert "<p>" in algorithm.shortHelpString()

        clone.initAlgorithm()
        parameters = clone.parameterDefinitions()
        names = [parameter.name() for parameter in parameters]

        assert parameters, clone.name()
        assert len(names) == len(set(names)), clone.name()
