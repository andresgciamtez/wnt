"""Regression checks for release translation and unit coordination."""
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from translation_catalog import sources, synchronize

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_without_qgis():
    assert synchronize(ROOT / 'wnt/i18n/wnt_es.ts', sources()) == []


def test_compiled_catalog_matches_every_translation():
    pytest.importorskip('qgis')
    from qgis.PyQt.QtCore import QTranslator
    translator = QTranslator()
    assert translator.load(str(ROOT / 'wnt/i18n/wnt_es.qm'))
    tree = ET.parse(ROOT / 'wnt/i18n/wnt_es.ts')
    for context in tree.findall('context'):
        for message in context.findall('message'):
            translation = message.find('translation')
            if translation is not None and translation.get('type') not in ('unfinished', 'vanished', 'obsolete'):
                assert translator.translate(context.findtext('name'), message.findtext('source').encode('utf-8')) == translation.text


def test_all_registered_toolbox_names(monkeypatch):
    pytest.importorskip('qgis')
    from .utilities import get_qgis_app
    get_qgis_app()
    from wnt.wnt_provider import WaterNetworkToolsProvider
    from qgis.PyQt.QtCore import QCoreApplication, QTranslator
    translator = QTranslator()
    assert translator.load(str(ROOT / 'wnt/i18n/wnt_es.qm'))
    QCoreApplication.installTranslator(translator)
    provider = WaterNetworkToolsProvider()
    try:
        provider.loadAlgorithms()
        assert provider.algorithms()
        for algorithm in provider.algorithms():
            monkeypatch.setenv('WNT_LOCALE', 'en')
            name, group = algorithm.displayName(), algorithm.group()
            monkeypatch.setenv('WNT_LOCALE', 'es')
            assert algorithm.displayName() == translator.translate('WaterNetworkTools', name)
            assert algorithm.group() == translator.translate('WaterNetworkTools', group)
    finally:
        QCoreApplication.removeTranslator(translator)


def test_hydrant_distance_parent():
    pytest.importorskip('qgis')
    from .utilities import get_qgis_app
    get_qgis_app()
    from wnt.processes.wnt_hydrant_pairs import HydrantPairsAlgorithm
    algorithm = HydrantPairsAlgorithm()
    algorithm.initAlgorithm()
    assert algorithm.parameterDefinition(algorithm.MAX_DISTANCE).parentParameterName() == algorithm.INPUT_HYDRANTS


@pytest.mark.parametrize('crs', ['EPSG:25830', 'EPSG:2263'])
@pytest.mark.parametrize('limit,count', [(100, 0), (200, 1)])
def test_hydrant_separation_in_layer_units(crs, limit, count):
    pytest.importorskip('qgis')
    from .utilities import get_qgis_app
    get_qgis_app()
    from qgis.core import (
        QgsVectorLayer, QgsFeature, QgsGeometry, QgsProcessingContext,
        QgsProcessingFeedback, QgsProcessingUtils,
    )
    from wnt.processes.wnt_hydrant_pairs import HydrantPairsAlgorithm
    layer = QgsVectorLayer(f'Point?crs={crs}&field=id:string', 'hydrants', 'memory')
    for identifier, x in [('a', 1000000), ('b', 1000150)]:
        feature = QgsFeature(layer.fields())
        feature.setAttributes([identifier])
        feature.setGeometry(QgsGeometry.fromWkt(f'POINT ({x} 200000)'))
        assert layer.dataProvider().addFeatures([feature])[0]
    algorithm = HydrantPairsAlgorithm()
    algorithm.initAlgorithm()
    context = QgsProcessingContext()
    result = algorithm.processAlgorithm({
        algorithm.INPUT_HYDRANTS: layer,
        algorithm.FIELD_ID: 'id',
        algorithm.MAX_DISTANCE: limit,
        algorithm.OUTPUT_PAIRS: 'memory:',
    }, context, QgsProcessingFeedback())
    output = QgsProcessingUtils.mapLayerFromString(result[algorithm.OUTPUT_PAIRS], context)
    assert output.crs() == layer.crs()
    assert output.featureCount() == count
    if count:
        assert next(output.getFeatures())['distance'] == pytest.approx(150)
