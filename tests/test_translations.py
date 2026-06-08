"""Tests for compiled Qt translations."""

import ast
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

from .utilities import get_qgis_app

from qgis.PyQt.QtCore import QTranslator
from wnt.processes.wnt_validate import ValidateAlgorithm

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


def test_processing_toolbox_entries_are_not_translated():
    """Processing toolbox entries keep their source English labels."""
    algorithm = ValidateAlgorithm()

    assert algorithm.displayName() == 'Validate'
    assert algorithm.group() == 'Graph'
