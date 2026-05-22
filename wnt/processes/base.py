"""Base classes for Water Network Tools processing algorithms."""

import re

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (
    QgsFeature,
    QgsField,
    QgsProcessingAlgorithm,
)

from ..i18n import tr

CODE_STYLE = 'color:#0057b8; font-weight:600;'
OUTPUT_MODE_NEW = 0
OUTPUT_MODE_UPDATE = 1
OUTPUT_MODE_OPTIONS = ('Create new output layer', 'Update input layer')


def style_help_html(message):
    """Improve readability of inline code fragments in Processing help text."""
    return message.replace('<code>', f'<code style="{CODE_STYLE}">')


def field_names(source):
    """Return the field names exposed by a vector source."""
    return set(source.fields().names())


def missing_fields(source, required_fields):
    """Return required fields that are not present in a vector source."""
    names = field_names(source)
    return [field for field in required_fields if field not in names]


def set_progress(feedback, start, end, count, total):
    if total:
        feedback.setProgress(start + (end - start) * count / total)


def parse_name_list(value):
    """Return stripped names from comma/semicolon-separated text."""
    return [item.strip() for item in re.split(r"[,;]", value or "") if item.strip()]


def qfield(name, field_type=QMetaType.QString):
    """Build a QGIS field."""
    return QgsField(name, field_type)


def field_index(fields, name):
    """Return a field index by name, or -1 when missing."""
    try:
        return fields.lookupField(name)
    except AttributeError:
        for index, field in enumerate(fields):
            if field.name() == name:
                return index
    return -1


def attributes_with_fields(feature, fields, updates=None):
    """Return feature attributes aligned to fields with optional updates."""
    updates = updates or {}
    attrs = list(feature.attributes())
    if len(attrs) < len(fields):
        attrs.extend([None] * (len(fields) - len(attrs)))
    for name, value in updates.items():
        index = field_index(fields, name)
        if index >= 0:
            attrs[index] = value
    return attrs


def feature_copy(feature, fields, updates=None, geometry=None):
    """Return a feature copy aligned to fields."""
    try:
        copied = QgsFeature(fields)
    except TypeError:
        try:
            copied = QgsFeature(feature)
        except TypeError:
            copied = feature
    copied.setGeometry(geometry if geometry is not None else feature.geometry())
    copied.setAttributes(attributes_with_fields(feature, fields, updates))
    return copied


def add_missing_fields(layer, field_defs):
    """Add missing fields to a vector layer and return updated fields."""
    fields = layer.fields()
    missing = [field for field in field_defs if field_index(fields, field.name()) < 0]
    if missing:
        provider = layer.dataProvider()
        if not provider.addAttributes(missing):
            raise RuntimeError("Could not add required fields to input layer")
        layer.updateFields()
    return layer.fields()


def _start_edit(layer):
    already_editing = bool(getattr(layer, "isEditable", lambda: False)())
    if not already_editing and not layer.startEditing():
        raise RuntimeError("Could not start editing input layer")
    return already_editing


def _finish_edit(layer, already_editing):
    if not already_editing and not layer.commitChanges():
        raise RuntimeError("Could not commit edits to input layer")


def _rollback_edit(layer, already_editing):
    if not already_editing:
        layer.rollBack()


def update_layer_attributes(layer, updates_by_feature_id):
    """Apply attribute updates to an editable vector layer with rollback."""
    already_editing = _start_edit(layer)
    try:
        for feature_id, updates in updates_by_feature_id.items():
            for field_idx, value in updates.items():
                if not layer.changeAttributeValue(feature_id, field_idx, value):
                    raise RuntimeError("Could not update input layer attributes")
        _finish_edit(layer, already_editing)
    except Exception:
        _rollback_edit(layer, already_editing)
        raise



def replace_layer_features(layer, features):
    """Replace all features in a vector layer with rollback."""
    already_editing = _start_edit(layer)
    try:
        feature_ids = [feature.id() for feature in layer.getFeatures()]
        if feature_ids and not layer.deleteFeatures(feature_ids):
            raise RuntimeError("Could not delete input layer features")
        if features and not layer.addFeatures(features):
            raise RuntimeError("Could not add replacement input layer features")
        _finish_edit(layer, already_editing)
    except Exception:
        _rollback_edit(layer, already_editing)
        raise


class WntProcessingAlgorithm(QgsProcessingAlgorithm):
    """Processing algorithm base class with a shared translation context."""

    def tr(self, message):
        """Return a translated string."""
        return style_help_html(tr(message))
