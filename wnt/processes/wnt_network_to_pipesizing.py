"""Export pipesizing input from network layers."""

import os
import re
from pathlib import Path

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from .base import WntProcessingAlgorithm, missing_fields
from .messages import error, finish, info, start


class NetworkToPipesizingAlgorithm(WntProcessingAlgorithm):
    """Build a pipesizing data file (.pro) from node and link data."""

    INPUT_NODES = 'INPUT_NODES'
    FIELD_PRESSURE = 'FIELD_PRESSURE'
    INPUT_LINES = 'INPUT_LINES'
    FIELD_SERIES = 'FIELD_SERIES'
    INPUT_EPANET = 'INPUT_EPANET'
    INPUT_CATALOG = 'INPUT_CATALOG'
    OUTPUT = 'OUTPUT'

    def createInstance(self):
        return NetworkToPipesizingAlgorithm()

    @staticmethod
    def _catalog_has_section_header(catalog_bytes):
        text = catalog_bytes.decode('utf-8')
        for line in text.splitlines():
            clean_line = line.partition('#')[0].strip()
            if clean_line.startswith('[') and clean_line.endswith(']'):
                return True
        return False

    @staticmethod
    def _catalog_series(catalog_bytes):
        series = set()
        for raw in catalog_bytes.decode('utf-8').splitlines():
            clean = raw.split('#', 1)[0].strip()
            if not clean:
                continue
            parts = clean.split()
            if len(parts) < 3:
                raise ValueError('Pipesizing catalog lines must contain: series diameter roughness')
            try:
                diameter = float(parts[1])
                roughness = float(parts[2])
            except ValueError as exc:
                raise ValueError('Pipesizing catalog diameter and roughness must be numeric') from exc
            if diameter <= 0 or roughness <= 0:
                raise ValueError('Pipesizing catalog diameter and roughness must be greater than zero')
            series.add(parts[0])
        if not series:
            raise ValueError('Pipesizing catalog is empty')
        return series

    @staticmethod
    def _relative_network_path(epanet_file, output_file):
        output_dir = Path(output_file).parent
        relative = os.path.relpath(str(epanet_file), str(output_dir))
        if re.search(r'\s', relative):
            raise ValueError('EPANET path relative to the .pro file must not contain spaces')
        return relative.replace('\\', '/')

    def name(self):
        return 'network_to_pipesizing'

    def displayName(self):
        return 'Network to pipesizing data file (.pro)'

    def group(self):
        return 'Export'

    def groupId(self):
        return 'export'

    def shortHelpString(self):
        return self.tr('''<p>Creates a pipesizing <code>.pro</code> data file.</p>
<ul>
<li>The required pressure must be stored in a node layer field.</li>
<li>The pipe series name must be stored in a link layer field.</li>
<li>The EPANET <code>.inp</code> file path is written relative to the <code>.pro</code> file.</li>
<li>The pipe catalog is selected directly as an external <code>.cat</code> file.</li>
</ul>
        ''')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NODES,
                self.tr('Input node layer'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_PRESSURE,
                self.tr('Required pressure field'),
                None,
                self.INPUT_NODES,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
                self.tr('Input link layer'),
                [QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_SERIES,
                self.tr('Pipe series field'),
                None,
                self.INPUT_LINES,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_EPANET,
                self.tr('EPANET file'),
                extension='inp'
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_CATALOG,
                self.tr('Pipesizing pipe catalog file'),
                extension='cat'
                )
            )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output pipesizing file'),
                fileFilter='*.pro'
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        nodes = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        pfield = self.parameterAsFields(parameters, self.FIELD_PRESSURE, context)[0]
        links = self.parameterAsSource(parameters, self.INPUT_LINES, context)
        sfield = self.parameterAsFields(parameters, self.FIELD_SERIES, context)[0]
        epanet_file = self.parameterAsFile(parameters, self.INPUT_EPANET, context)
        catalog_input_file = self.parameterAsFile(parameters, self.INPUT_CATALOG, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        if nodes.sourceCrs() != links.sourceCrs():
            error(feedback, 'Layers have different CRS')
            return {}
        missing = missing_fields(nodes, ['id']) + missing_fields(links, ['id'])
        if missing:
            error(feedback, 'Missing required fields: ' + ', '.join(missing))
            return {}
        if not Path(epanet_file).exists():
            error(feedback, 'EPANET file not found: ' + epanet_file)
            return {}
        catalog_source = Path(catalog_input_file)
        if not catalog_source.exists():
            error(feedback, 'Pipesizing pipe catalog file not found: ' + catalog_input_file)
            return {}

        try:
            catalog_bytes = catalog_source.read_bytes()
            if self._catalog_has_section_header(catalog_bytes):
                error(feedback, 'Pipesizing pipe catalog must not contain section headers')
                return {}
            known_series = self._catalog_series(catalog_bytes)
            network_path = self._relative_network_path(epanet_file, output_file)
        except (UnicodeDecodeError, ValueError) as exc:
            error(feedback, str(exc))
            return {}

        catalog_file = Path(output_file).with_suffix('.cat')
        catalog_file.write_bytes(catalog_bytes)

        pressure_lines = []
        for feature in nodes.getFeatures():
            value = feature[pfield]
            if value not in (None, ''):
                pressure_lines.append('{}    {}'.format(feature['id'], value))

        pipe_lines = []
        unknown_series = set()
        for feature in links.getFeatures():
            value = feature[sfield]
            if value in (None, ''):
                continue
            series_name = str(value)
            if series_name not in known_series:
                unknown_series.add(series_name)
            pipe_lines.append('{}    {}'.format(feature['id'], series_name))
        if unknown_series:
            error(feedback, 'Pipes reference unknown series: ' + ', '.join(sorted(unknown_series)))
            return {}

        lines = [
            '# File generated automatically by Water Network Tools',
            '',
            '[NETWORK]',
            network_path,
            '',
            '[PIPE_CATALOG]',
            catalog_file.name,
            '',
            '[PRESSURES]',
            '# node_id   min_pressure',
        ]
        lines.extend(pressure_lines)
        lines.extend(['', '[PIPES]', '# pipe_id   series_name'])
        lines.extend(pipe_lines)
        Path(output_file).write_text('\n'.join(lines) + '\n', encoding='utf-8')

        start(feedback, self.displayName())
        info(feedback, 'Nodes with minimum pressure', len(pressure_lines))
        info(feedback, 'Pipes to size', len(pipe_lines))
        info(feedback, 'Series defined', len(known_series))
        info(feedback, 'Pipe catalog file', catalog_file)
        info(feedback, 'EPANET file', network_path)
        info(feedback, 'Output file', output_file)
        finish(feedback)
        if feedback.isCanceled():
            return {}
        return {self.OUTPUT: output_file}
