"""Tests for the QGIS runtime environment."""


from pathlib import Path
import pytest
from qgis.core import (
    QgsProviderRegistry,
    QgsCoordinateReferenceSystem,
    QgsRasterLayer)
from wnt.processes.wnt_elevation_from_raster import ElevationFromRasterAlgorithm
from wnt.wnt_provider import WaterNetworkToolsProvider

from .utilities import get_qgis_app
QGIS_APP = get_qgis_app()


pytestmark = pytest.mark.qgis


def test_qgis_environment_has_required_providers():
    """QGIS exposes the providers used by the plugin tests."""
    providers = QgsProviderRegistry.instance().providerList()

    assert 'gdal' in providers
    assert 'ogr' in providers


def test_projection_parsing_and_raster_crs():
    """QGIS parses WGS84 CRS definitions and assigns CRS to test rasters."""
    crs = QgsCoordinateReferenceSystem()
    wkt = (
        'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",'
        'SPHEROID["WGS_1984",6378137.0,298.257223563]],'
        'PRIMEM["Greenwich",0.0],UNIT["Degree",'
        '0.0174532925199433]]')

    assert crs.createFromWkt(wkt)
    assert crs.authid() == 'EPSG:4326'

    raster_path = Path(__file__).with_name('tenbytenraster.asc')
    layer = QgsRasterLayer(str(raster_path), 'TestRaster')

    assert layer.isValid()
    assert layer.crs().authid() in {'EPSG:4326', 'OGC:CRS84'}


def test_raster_elevation_field_parameter_is_bound_to_node_layer():
    """The elevation field selector is populated from the node input."""
    algorithm = ElevationFromRasterAlgorithm()
    algorithm.initAlgorithm()

    parameter = algorithm.parameterDefinition(algorithm.FIELD_ELEVATION)

    assert parameter.parentLayerParameterName() == algorithm.INPUT_NODES


def test_processing_parameters_have_unique_names():
    """Every algorithm exposes unique parameter names."""
    provider = WaterNetworkToolsProvider()
    provider.loadAlgorithms()

    for algorithm in provider.algorithms():
        names = [parameter.name() for parameter in algorithm.parameterDefinitions()]

        assert len(names) == len(set(names)), algorithm.name()
