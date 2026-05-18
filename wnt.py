"""QGIS plugin bootstrap."""

import os
import sys
import inspect
from pathlib import Path

from qgis.PyQt.QtCore import QCoreApplication, QSettings, QTranslator
from qgis.core import QgsApplication
from .wnt_provider import WaterNetworkToolsProvider

cmd_folder = os.path.split(inspect.getfile(inspect.currentframe()))[0]

if cmd_folder not in sys.path:
    sys.path.insert(0, cmd_folder)


class WaterNetworkToolsPlugin():
    """ Main class."""
    def __init__(self):
        self.provider = None
        self.translator = None
        self._load_translation()

    def _load_translation(self):
        """Load the compiled translation matching the QGIS locale."""
        locale = QSettings().value('locale/userLocale', '', type=str)[:2]
        if not locale:
            return

        locale_path = Path(__file__).resolve().parent / 'i18n' / f'wnt_{locale}.qm'
        if not locale_path.is_file():
            return

        translator = QTranslator()
        if translator.load(str(locale_path)):
            QCoreApplication.installTranslator(translator)
            self.translator = translator

    def initProcessing(self):
        """Init Processing provider for QGIS >= 3.8."""
        self.provider = WaterNetworkToolsProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)
        if self.translator is not None:
            QCoreApplication.removeTranslator(self.translator)
            self.translator = None

