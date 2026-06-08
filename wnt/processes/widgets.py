"""Processing widget helpers used by Water Network Tools algorithms."""

from pathlib import Path

from qgis.PyQt.QtWidgets import QComboBox
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper

from ..utils.utils_tin import surface_names


class LandXmlSurfaceWidgetWrapper(QgsAbstractProcessingParameterWidgetWrapper):
    """Editable combo box populated from the selected LandXML file."""

    def createWidget(self):
        self._combo = QComboBox()
        self._combo.setEditable(True)
        self._combo.currentTextChanged.connect(
            lambda _text: self.widgetValueHasChanged.emit(self)
        )
        self._file_wrapper = None
        return self._combo

    def postInitialize(self, wrappers):
        file_parameter = self.parameterDefinition().metadata().get("landxml_file_parameter")
        for wrapper in wrappers:
            try:
                parameter_name = wrapper.parameterDefinition().name()
            except AttributeError:
                continue
            if parameter_name == file_parameter:
                self._file_wrapper = wrapper
                wrapper.widgetValueHasChanged.connect(lambda _wrapper: self._refresh_surfaces())
                break
        self._refresh_surfaces()

    def setWidgetValue(self, value, context):
        self._set_combo_text(str(value or ""))

    def widgetValue(self):
        return self._combo.currentText().strip()

    def _selected_file(self):
        if self._file_wrapper is None:
            return ""
        try:
            return str(self._file_wrapper.widgetValue() or "")
        except AttributeError:
            return str(self._file_wrapper.parameterValue() or "")

    def _refresh_surfaces(self):
        current = self.widgetValue()
        names = []
        landxml_file = self._selected_file()
        if landxml_file and Path(landxml_file).is_file():
            try:
                names = surface_names(landxml_file)
            except Exception:
                names = []

        self._combo.blockSignals(True)
        self._combo.clear()
        self._combo.addItems(names)
        if current:
            self._set_combo_text(current)
        elif names:
            self._combo.setCurrentText(names[0])
        self._combo.blockSignals(False)

    def _set_combo_text(self, value):
        index = self._combo.findText(value)
        if index >= 0:
            self._combo.setCurrentIndex(index)
        else:
            self._combo.setEditText(value)
