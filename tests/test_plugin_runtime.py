"""Tests for the QGIS plugin bootstrap object."""

from pathlib import Path

import pytest

import wnt
from wnt.wnt import WaterNetworkToolsPlugin

from .utilities import get_qgis_app


QGIS_APP = get_qgis_app()


pytestmark = pytest.mark.qgis


def test_class_factory_returns_plugin_instance():
    assert isinstance(wnt.classFactory(None), WaterNetworkToolsPlugin)


def test_plugin_processing_lifecycle():
    plugin = WaterNetworkToolsPlugin()

    assert plugin.provider is None
    plugin.initGui()
    assert plugin.provider is not None

    plugin.unload()
    assert plugin.translator is None


def test_unload_removes_loaded_translator(monkeypatch):
    plugin = WaterNetworkToolsPlugin()
    plugin.initProcessing()
    translator = object()
    removed = []
    plugin.translator = translator

    monkeypatch.setattr("wnt.wnt.QCoreApplication.removeTranslator", removed.append)

    plugin.unload()

    assert removed == [translator]
    assert plugin.translator is None


def test_load_translation_branches(monkeypatch, tmp_path):
    plugin = WaterNetworkToolsPlugin()
    plugin.translator = None

    class EmptySettings:
        def value(self, *args, **kwargs):
            return ""

    monkeypatch.setattr("wnt.wnt.QSettings", EmptySettings)
    plugin._load_translation()
    assert plugin.translator is None

    class MissingSettings:
        def value(self, *args, **kwargs):
            return "zz"

    monkeypatch.setattr("wnt.wnt.QSettings", MissingSettings)
    plugin._load_translation()
    assert plugin.translator is None

    qm = tmp_path / "wnt_yy.qm"
    qm.write_bytes(b"not a real catalog")

    class FakePath:
        def __init__(self, value):
            self.value = Path(value)

        def resolve(self):
            return self

        @property
        def parent(self):
            return self

        def __truediv__(self, other):
            return FakePath(qm if other == "wnt_yy.qm" else self.value / other)

        def is_file(self):
            return True

        def __str__(self):
            return str(qm)

    class CatalogSettings:
        def value(self, *args, **kwargs):
            return "yy"

    class FakeTranslator:
        def load(self, path):
            assert path == str(qm)
            return True

    installed = []

    monkeypatch.setattr("wnt.wnt.QSettings", CatalogSettings)
    monkeypatch.setattr("wnt.wnt.Path", FakePath)
    monkeypatch.setattr("wnt.wnt.QTranslator", FakeTranslator)
    monkeypatch.setattr("wnt.wnt.QCoreApplication.installTranslator", installed.append)

    plugin._load_translation()

    assert plugin.translator is installed[0]
