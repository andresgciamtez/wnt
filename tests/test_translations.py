"""Tests for compiled Qt translations."""

import ast
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

from .utilities import get_qgis_app

from qgis.PyQt.QtCore import QTranslator

QGIS_APP = get_qgis_app()


pytestmark = pytest.mark.qgis


def test_qgis_translations(monkeypatch):
    """Water Network Tools translations load from the compiled plugin catalog."""
    monkeypatch.delenv('LANG', raising=False)

    plugin_dir = Path(__file__).resolve().parents[1] / 'wnt'
    file_path = plugin_dir / 'i18n' / 'wnt_es.qm'

    if not file_path.is_file():
        pytest.skip(f'Compiled translation file not found: {file_path}')

    translator = QTranslator()

    assert translator.load(str(file_path))

    source_file = plugin_dir / 'processes' / 'wnt_validate.py'
    tree = ast.parse(source_file.read_text(encoding='utf-8-sig'))
    help_source = next(
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == 'tr'
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and 'Analyses the network graph' in node.args[0].value
    )

    translated_help = translator.translate('WaterNetworkTools', help_source)

    assert translated_help.startswith('<p>Analiza el grafo de la red')
    assert '<code>problems</code>' in translated_help


def test_translation_catalog_matches_translatable_sources():
    """Every current tr() string is present in the Spanish catalog."""
    plugin_dir = Path(__file__).resolve().parents[1] / 'wnt'
    catalog = ET.parse(plugin_dir / 'i18n' / 'wnt_es.ts')
    catalog_sources = {
        source.text.replace('\r\n', '\n').replace('\r', '\n')
        for source in catalog.findall('.//source')
        if source.text
    }
    code_sources = set()

    for source_file in plugin_dir.rglob('*.py'):
        tree = ast.parse(source_file.read_text(encoding='utf-8-sig'))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue

            function = node.func
            is_translation_call = (
                isinstance(function, ast.Attribute) and function.attr == 'tr'
            ) or (
                isinstance(function, ast.Name) and function.id == 'tr'
            )
            if not is_translation_call:
                continue

            argument = node.args[0]
            if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                code_sources.add(
                    argument.value.replace('\r\n', '\n').replace('\r', '\n')
                )

    assert code_sources <= catalog_sources


def test_spanish_translation_catalog_has_no_unfinished_entries():
    """Spanish catalog entries must be usable by QGIS, not left unfinished."""
    plugin_dir = Path(__file__).resolve().parents[1] / 'wnt'
    catalog = ET.parse(plugin_dir / 'i18n' / 'wnt_es.ts')
    unfinished = catalog.findall('.//translation[@type="unfinished"]')
    empty = [
        translation for translation in catalog.findall('.//translation')
        if not ''.join(translation.itertext()).strip()
    ]

    assert unfinished == []
    assert empty == []



def test_spanish_catalog_has_no_mojibake_markers():
    """Spanish translations should keep UTF-8 accents readable."""
    plugin_dir = Path(__file__).resolve().parents[1] / 'wnt'
    text = (plugin_dir / 'i18n' / 'wnt_es.ts').read_text(encoding='utf-8')

    for marker in ('\u00c3', '\u00c2', '\ufffd', '\u00e2', '\u00c6', '\u0192', '\u2122'):
        assert marker not in text


def test_processing_toolbox_entries_use_spanish_catalog():
    """Processing toolbox entries are translatable and present in the catalog."""
    plugin_dir = Path(__file__).resolve().parents[1] / 'wnt'
    file_path = plugin_dir / 'i18n' / 'wnt_es.qm'
    translator = QTranslator()

    if not file_path.is_file():
        pytest.skip(f'Compiled translation file not found: {file_path}')

    assert translator.load(str(file_path))
    expected_names = {
        'processes/wnt_network_to_epanet.py': (
            'Network to epanet file (.inp)',
            'Red a archivo EPANET (.inp)',
        ),
        'processes/wnt_network_to_pipesizing.py': (
            'Network to pipesizing data file (.pro)',
            'Red a archivo de datos pipesizing (.pro)',
        ),
        'processes/wnt_network_to_xml.py': ('Network to XML', 'Red a XML'),
        'processes/wnt_hydrant_pairs.py': ('Hydrant pairs', 'Pares de hidrantes'),
        'processes/wnt_classify.py': ('Classify', 'Clasificar'),
        'processes/wnt_node_degrees.py': ('Node degrees', 'Grados de nodo'),
        'processes/wnt_network_from_xml.py': ('Network from XML', 'Red desde XML'),
        'processes/wnt_results_from_epanet.py': (
            'Results from EPANET',
            'Resultados de EPANET',
        ),
        'processes/wnt_merge_networks.py': ('Merge networks', 'Fusionar redes'),
        'processes/wnt_elevation_from_tin.py': (
            'Node elevation from TIN (LandXML)',
            'Elevación de nodos desde TIN (LandXML)',
        ),
        'processes/wnt_elevation_from_raster.py': (
            'Node elevation from DEM',
            'Elevación de nodos desde MDE',
        ),
        'processes/wnt_split_lines_at_points.py': (
            'Split lines at points',
            'Dividir líneas en puntos',
        ),
    }
    expected_toolbox_text = {
        'Build': 'Construir',
        'Demand': 'Demanda',
        'Export': 'Exportar',
        'Fire': 'Incendio',
        'Graph': 'Grafo',
        'Import': 'Importar',
        'Modify': 'Modificar',
        'Network names': 'Nombres de red',
        'Links': 'Links de salida',
        'Create new output layer': 'Crear capa de salida nueva',
        'Update input layer': 'Actualizar capa de entrada',
    }

    for source, translation in expected_toolbox_text.items():
        assert translator.translate('WaterNetworkTools', source) == translation

    for source_path, (source, translation) in expected_names.items():
        assert translator.translate('WaterNetworkTools', source) == translation
        tree = ast.parse((plugin_dir / source_path).read_text(encoding='utf-8-sig'))
        display_name_functions = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == 'displayName'
        ]
        returns = [
            return_node.value
            for function in display_name_functions
            for return_node in ast.walk(function)
            if isinstance(return_node, ast.Return)
        ]

        assert any(
            isinstance(return_value, ast.Call)
            and isinstance(return_value.func, ast.Attribute)
            and return_value.func.attr == 'tr'
            and return_value.args
            and isinstance(return_value.args[0], ast.Constant)
            and return_value.args[0].value == source
            for return_value in returns
        )

    network_from_xml = ast.parse(
        (plugin_dir / 'processes' / 'wnt_network_from_xml.py').read_text(
            encoding='utf-8-sig'
        )
    )
    help_source = next(
        node.args[0].value
        for node in ast.walk(network_from_xml)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == 'tr'
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and 'Imports network node and link layers from XML' in node.args[0].value
    )
    translated_help = translator.translate('WaterNetworkTools', help_source)

    assert translated_help.startswith('<p>Importa capas de nodos y links')
    assert 'Imports network node and link layers from XML' not in translated_help
