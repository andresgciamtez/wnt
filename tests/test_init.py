"""Tests for plugin metadata."""


import logging
import configparser
from pathlib import Path

LOGGER = logging.getLogger('QGIS')


def test_metadata_required_fields():
    """Plugin metadata includes the fields required by the QGIS repository."""
    required_metadata = {
        'name',
        'description',
        'version',
        'qgisMinimumVersion',
        'email',
        'author',
    }

    file_path = Path(__file__).resolve().parents[1] / 'metadata.txt'
    LOGGER.info(file_path)

    parser = configparser.ConfigParser()
    parser.optionxform = str
    parser.read(file_path)

    assert parser.has_section('general'), (
        f'Cannot find a section named "general" in {file_path}'
    )

    metadata = dict(parser.items('general'))
    missing = required_metadata - set(metadata)

    assert not missing, (
        f'Missing metadata fields in {file_path}: {", ".join(sorted(missing))}'
    )


def test_metadata_icon_exists():
    """The icon declared in metadata points to a packaged resource."""
    plugin_dir = Path(__file__).resolve().parents[1]

    parser = configparser.ConfigParser()
    parser.read(plugin_dir / 'metadata.txt')

    icon_path = plugin_dir / parser.get('general', 'icon')

    assert icon_path.is_file()

