"""Tests for the QGIS plugin bootstrap object."""

from pathlib import Path

import pytest

pytest.importorskip("qgis")

import wnt
from wnt.wnt import WaterNetworkToolsPlugin
from wnt.wnt_provider import WaterNetworkToolsProvider

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



def test_unload_without_init_processing_does_not_fail():
    plugin = WaterNetworkToolsPlugin()

    plugin.unload()

    assert plugin.provider is None


def test_provider_keeps_loading_after_algorithm_import_error(monkeypatch):
    added = []

    class FakeModule:
        def __getattr__(self, name):
            return lambda: name

    def fake_import_module(module_name, package=None):
        if module_name.endswith("wnt_assign_demand"):
            raise ImportError("broken optional dependency")
        return FakeModule()

    class TestProvider(WaterNetworkToolsProvider):
        def __init__(self):
            self.load_errors = []

        def addAlgorithm(self, algorithm):
            added.append(algorithm)

    monkeypatch.setattr("wnt.wnt_provider.import_module", fake_import_module)
    provider = TestProvider()

    provider.loadAlgorithms()

    assert provider.load_errors == [("AssignDemandAlgorithm", "broken optional dependency")]
    assert added


def test_load_translation_branches(monkeypatch, tmp_path):
    plugin = WaterNetworkToolsPlugin()
    plugin.translator = None

    monkeypatch.setattr("wnt.wnt._locale_prefix", lambda: "")
    plugin._load_translation()
    assert plugin.translator is None

    monkeypatch.setattr("wnt.wnt._locale_prefix", lambda: "zz")
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

    class FakeTranslator:
        def load(self, path):
            assert path == str(qm)
            return True

    installed = []

    monkeypatch.setattr("wnt.wnt._locale_prefix", lambda: "yy")
    monkeypatch.setattr("wnt.wnt.Path", FakePath)
    monkeypatch.setattr("wnt.wnt.QTranslator", FakeTranslator)
    monkeypatch.setattr("wnt.wnt.QCoreApplication.installTranslator", installed.append)

    plugin._load_translation()

    assert plugin.translator is installed[0]
