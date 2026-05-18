"""Tests for compiled Qt translations."""

import ast
from pathlib import Path
import pytest

from .utilities import get_qgis_app

from qgis.PyQt.QtCore import QTranslator
from wnt.processes.wnt_validate import ValidateAlgorithm

QGIS_APP = get_qgis_app()


pytestmark = pytest.mark.qgis


def test_qgis_translations(monkeypatch):
    """Water Network Tools translations load from the compiled plugin catalog."""
    monkeypatch.delenv('LANG', raising=False)

    file_path = Path(__file__).resolve().parents[1] / 'i18n' / 'wnt_es.qm'

    if not file_path.is_file():
        pytest.skip(f'Compiled translation file not found: {file_path}')

    translator = QTranslator()

    assert translator.load(str(file_path))

    source_file = Path(__file__).resolve().parents[1] / 'processes' / 'wnt_validate.py'
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


def test_processing_toolbox_entries_are_not_translated():
    """Processing toolbox entries keep their source English labels."""
    algorithm = ValidateAlgorithm()

    assert algorithm.displayName() == 'Validate'
    assert algorithm.group() == 'Graph'
