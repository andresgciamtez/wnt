"""Export pipesizing input from network layers."""

import os
import re
from pathlib import Path

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination,
                       QgsProcessingParameterNumber)
from .base import WntProcessingAlgorithm, missing_fields
from .messages import error, finish, info, start, warning


class NetworkToPipesizingAlgorithm(WntProcessingAlgorithm):
    """Build a pipesizing data file (.pro) from node and link data."""

    INPUT_NODES = 'INPUT_NODES'
    FIELD_PRESSURE = 'FIELD_PRESSURE'
    FIELD_PRESSURE_FIRE = 'FIELD_PRESSURE_FIRE'
    INPUT_LINES = 'INPUT_LINES'
    FIELD_SERIES = 'FIELD_SERIES'
    INPUT_FIRE_SCENARIOS = 'INPUT_FIRE_SCENARIOS'
    FIELD_FIRE_FLOW = 'FIELD_FIRE_FLOW'
    FIRE_FLOW = 'FIRE_FLOW'
    PEAK_FACTOR = 'PEAK_FACTOR'
    FIRE_FACTOR = 'FIRE_FACTOR'
    INPUT_EPANET = 'INPUT_EPANET'
    INPUT_CATALOG = 'INPUT_CATALOG'
    OUTPUT = 'OUTPUT'
    MIN_FACTOR = 0.01
    MAX_FACTOR = 100.0
    DEFAULT_FIRE_FLOW_NAME = 'DEFAULT'

    def createInstance(self):
        return NetworkToPipesizingAlgorithm()

    @staticmethod
    def _strip_catalog_comment(line):
        """Return a catalog line without supported inline comments."""
        return line.split(';', 1)[0].split('#', 1)[0].strip()

    @classmethod
    def _catalog_has_section_header(cls, catalog_bytes):
        text = catalog_bytes.decode('utf-8')
        for line in text.splitlines():
            clean_line = cls._strip_catalog_comment(line)
            if clean_line.startswith('[') and clean_line.endswith(']'):
                return True
        return False

    @classmethod
    def _catalog_series(cls, catalog_bytes):
        series = set()
        for raw in catalog_bytes.decode('utf-8').splitlines():
            clean = cls._strip_catalog_comment(raw)
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

    @staticmethod
    def _flow_setting_name(value):
        name = str(value).strip()
        return name if name.upper().startswith('FLOW_') else 'FLOW_' + name

    @classmethod
    def _validate_factor(cls, value, label):
        if value < cls.MIN_FACTOR or value > cls.MAX_FACTOR:
            raise ValueError('{} must be between {} and {}'.format(label, cls.MIN_FACTOR, cls.MAX_FACTOR))

    @staticmethod
    def _atomic_write_outputs(output_file, catalog_file, pro_text, catalog_bytes):
        output_path = Path(output_file)
        catalog_path = Path(catalog_file)
        output_tmp = output_path.with_name(output_path.name + '.tmp')
        catalog_tmp = catalog_path.with_name(catalog_path.name + '.tmp')
        try:
            output_tmp.write_text(pro_text, encoding='utf-8')
            catalog_tmp.write_bytes(catalog_bytes)
            catalog_tmp.replace(catalog_path)
            output_tmp.replace(output_path)
        finally:
            for path in (output_tmp, catalog_tmp):
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass

    def name(self):
        return 'network_to_pipesizing'

    def displayName(self):
        return self.tr('Network to pipesizing data file (.pro)')

    def group(self):
        return self.tr('Export')

    def groupId(self):
        return 'export'

    def shortHelpString(self):
        return self.tr('''<p>Creates a pipesizing <code>.pro</code> data file.</p>
<ul>
<li>The required peak-flow and fire-flow pressures must be stored in node layer fields.</li>
<li>The pipe series name must be stored in a link layer field.</li>
<li>Optional hydrant pair/fire scenario lines can be written from a hydrant pairs layer.</li>
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
                self.tr('Required peak pressure field'),
                None,
                self.INPUT_NODES,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_PRESSURE_FIRE,
                self.tr('Required fire pressure field'),
                None,
                self.INPUT_NODES,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.PEAK_FACTOR,
                self.tr('Peak demand factor'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.0,
                minValue=self.MIN_FACTOR,
                maxValue=self.MAX_FACTOR
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.FIRE_FACTOR,
                self.tr('Fire demand factor'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=1.0,
                minValue=self.MIN_FACTOR,
                maxValue=self.MAX_FACTOR
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
            QgsProcessingParameterFeatureSource(
                self.INPUT_FIRE_SCENARIOS,
                self.tr('Hydrant pairs / fire scenarios layer'),
                [QgsProcessing.TypeVectorLine],
                optional=True
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_FIRE_FLOW,
                self.tr('Fire flow name field'),
                None,
                self.INPUT_FIRE_SCENARIOS,
                allowMultiple=False,
                optional=True
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.FIRE_FLOW,
                self.tr('Fire flow value'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.0,
                minValue=0.0
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

    def checkParameterValues(self, parameters, context):
        try:
            self._validate_factor(self.parameterAsDouble(parameters, self.PEAK_FACTOR, context), 'Peak demand factor')
            self._validate_factor(self.parameterAsDouble(parameters, self.FIRE_FACTOR, context), 'Fire demand factor')
        except ValueError as exc:
            return False, self.tr(str(exc))
        return super().checkParameterValues(parameters, context)

    def processAlgorithm(self, parameters, context, feedback):
        nodes = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        pfield = self.parameterAsFields(parameters, self.FIELD_PRESSURE, context)[0]
        fire_pressure_fields = self.parameterAsFields(parameters, self.FIELD_PRESSURE_FIRE, context)
        fire_pressure_field = fire_pressure_fields[0] if fire_pressure_fields else pfield
        peak_factor = self.parameterAsDouble(parameters, self.PEAK_FACTOR, context)
        fire_factor = self.parameterAsDouble(parameters, self.FIRE_FACTOR, context)
        links = self.parameterAsSource(parameters, self.INPUT_LINES, context)
        sfield = self.parameterAsFields(parameters, self.FIELD_SERIES, context)[0]
        try:
            scenarios = self.parameterAsSource(parameters, self.INPUT_FIRE_SCENARIOS, context)
        except (KeyError, TypeError):
            scenarios = None
        try:
            fire_flow_fields = self.parameterAsFields(parameters, self.FIELD_FIRE_FLOW, context)
        except (KeyError, TypeError):
            fire_flow_fields = []
        fire_flow_field = fire_flow_fields[0] if fire_flow_fields else ''
        fire_flow_value = self.parameterAsDouble(parameters, self.FIRE_FLOW, context)
        epanet_file = self.parameterAsFile(parameters, self.INPUT_EPANET, context)
        catalog_input_file = self.parameterAsFile(parameters, self.INPUT_CATALOG, context)
        output_file = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        if nodes.sourceCrs() != links.sourceCrs():
            error(feedback, 'Layers have different CRS')
        missing = missing_fields(nodes, ['id']) + missing_fields(links, ['id'])
        if scenarios is not None:
            if nodes.sourceCrs() != scenarios.sourceCrs():
                error(feedback, 'Layers have different CRS')
            missing += missing_fields(scenarios, ['hydrant_1', 'hydrant_2'])
        if missing:
            error(feedback, 'Missing required fields: ' + ', '.join(missing))
        try:
            self._validate_factor(peak_factor, 'Peak demand factor')
            self._validate_factor(fire_factor, 'Fire demand factor')
        except ValueError as exc:
            error(feedback, str(exc))
        if not Path(epanet_file).exists():
            error(feedback, 'EPANET file not found: ' + epanet_file)
        catalog_source = Path(catalog_input_file)
        if not catalog_source.exists():
            error(feedback, 'Pipesizing pipe catalog file not found: ' + catalog_input_file)

        try:
            catalog_bytes = catalog_source.read_bytes()
            if self._catalog_has_section_header(catalog_bytes):
                error(feedback, 'Pipesizing pipe catalog must not contain section headers')
            known_series = self._catalog_series(catalog_bytes)
            network_path = self._relative_network_path(epanet_file, output_file)
        except (UnicodeDecodeError, ValueError) as exc:
            error(feedback, str(exc))

        pressure_lines = []
        for feature in nodes.getFeatures():
            peak_value = feature[pfield]
            fire_value = feature[fire_pressure_field]
            if peak_value not in (None, '') and fire_value not in (None, ''):
                pressure_lines.append('{}    {}    {}'.format(feature['id'], peak_value, fire_value))

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

        fire_scenario_lines = []
        flow_names = set()
        if scenarios is not None:
            if fire_flow_value <= 0:
                error(feedback, 'Fire flow value must be greater than zero when fire scenarios are selected')
            for feature in scenarios.getFeatures():
                flow_name = feature[fire_flow_field] if fire_flow_field else self.DEFAULT_FIRE_FLOW_NAME
                if flow_name in (None, ''):
                    flow_name = self.DEFAULT_FIRE_FLOW_NAME
                flow_names.add(self._flow_setting_name(flow_name))
                fire_scenario_lines.append('{}    {}    {}    {}'.format(
                    feature['hydrant_1'],
                    flow_name,
                    feature['hydrant_2'],
                    flow_name,
                ))

        catalog_file = Path(output_file).with_suffix('.cat')
        if catalog_file.exists():
            warning(feedback, f"Existing pipe catalog will be overwritten: {catalog_file}")
        lines = [
            '; File generated automatically by Water Network Tools',
            '',
            '[SETTINGS]',
            'epanet_file {}'.format(network_path),
            'catalog {}'.format(catalog_file.name),
            'peak_factor {}'.format(peak_factor),
            'fire_factor {}'.format(fire_factor),
        ]
        for flow_name in sorted(flow_names):
            lines.append('{} {}'.format(flow_name, fire_flow_value))
        lines.extend(['', '[PRESSURES]', '; node_id   min_peak_pressure   min_fire_pressure'])
        lines.extend(pressure_lines)
        lines.extend(['', '[FIRE_SCENARIOS]', '; node_id   fire_flow   node_id   fire_flow'])
        lines.extend(fire_scenario_lines)
        lines.extend(['', '[PIPES]', '; pipe_id   series_name'])
        lines.extend(pipe_lines)

        try:
            self._atomic_write_outputs(
                output_file,
                catalog_file,
                '\n'.join(lines) + '\n',
                catalog_bytes,
            )
        except OSError as exc:
            error(feedback, str(exc))

        start(feedback, self.displayName())
        info(feedback, 'Nodes with minimum pressure', len(pressure_lines))
        info(feedback, 'Pipes to size', len(pipe_lines))
        info(feedback, 'Fire scenarios', len(fire_scenario_lines))
        info(feedback, 'Series defined', len(known_series))
        info(feedback, 'Pipe catalog file', catalog_file)
        info(feedback, 'EPANET file', network_path)
        info(feedback, 'Output file', output_file)
        finish(feedback)
        if feedback.isCanceled():
            return {}
        return {self.OUTPUT: output_file}
