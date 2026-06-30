"""Pytest configuration for Water Network Tools."""

from pathlib import Path
import sys

import pytest


PLUGIN_PARENT = Path(__file__).resolve().parents[1]

if str(PLUGIN_PARENT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_PARENT))

@pytest.fixture(autouse=True)
def qgis_tests_use_english_locale(monkeypatch):
    """Keep tests independent from the user's persisted QGIS UI language."""
    try:
        from qgis.PyQt.QtCore import QSettings
    except ImportError:
        yield
        return

    monkeypatch.setenv('WNT_LOCALE', 'en')
    settings = QSettings()
    previous_locale = settings.value('locale/userLocale', '')
    settings.setValue('locale/userLocale', 'en')

    try:
        from wnt.i18n import _TS_CACHE
    except ImportError:
        _TS_CACHE = None
    if _TS_CACHE is not None:
        _TS_CACHE.clear()

    try:
        yield
    finally:
        settings.setValue('locale/userLocale', previous_locale)
        if _TS_CACHE is not None:
            _TS_CACHE.clear()

