"""Export PPNO sizing input from network layers."""

from pathlib import Path

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from .base import WntProcessingAlgorithm
from ..utils import utils_parser as parser
from .messages import error, finish, info, start

class PpnoFromNetworkAlgorithm(WntProcessingAlgorithm):
    """
    Build a ppno data file (.ext) from node and link data.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    FIELD_PRESSURE = 'FIELD_PRESSURE'
    INPUT_LINES = 'INPUT_LINES'
    FIELD_SERIES = 'FIELD_SERIES'
    INPUT_ALGORITHMS = 'INPUT_ALGORITHMS'
    INPUT_EPANET = 'INPUT_EPANET'
    INPUT_TEMPLATE = 'INPUT_TEMPLATE'
    OUTPUT = 'OUTPUT'
    ALGORITHMS = ('DE', 'DA', 'NSGA2', 'MOEAD', 'MACO', 'PSO')


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return PpnoFromNetworkAlgorithm()

    @staticmethod
    def _options_with_algorithms(options, algorithms):
        filtered_options = []
        for line in options:
            tokens = parser.parse_tokens(line)
            if tokens and tokens[0].lower() in ('algorithm', 'algorithms'):
                continue
            filtered_options.append(line)

        if algorithms:
            filtered_options.append(parser.format_tokens(('Algorithm', *algorithms)))
        return filtered_options

    @staticmethod
    def _resolve_template_path(template_file, raw_path):
        path = Path(raw_path)
        if path.is_absolute():
            return path

        template_dir = Path(template_file).parent
        candidates = [path, template_dir / path, template_dir / path.name]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[-1]

    @staticmethod
    def _catalog_has_section_header(catalog_bytes):
        text = catalog_bytes.decode('latin-1')
        for line in text.splitlines():
            clean_line = line.partition(';')[0].strip()
            if clean_line.startswith('[') and clean_line.endswith(']'):
                return True
        return False
    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'ppno_from_network'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'ppno data file from network'

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return 'Export'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'export'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''<p>Creates a PPNO <code>.ext</code> data file for pipe sizing.</p>
<ul>
<li>The required pressure must be stored in a node layer field.</li>
<li>The pipe group must be stored in a link layer field.</li>
<li>The EPANET <code>.inp</code> file must contain the model to optimize.</li>
<li>The PPNO template must reference a pipe catalog in <code>[PIPE_CATALOG]</code>.</li>
</ul>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT SOURCES
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
                'Required pressure',
                self.INPUT_NODES,
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
                self.tr('Pipe group field'),
                'Pipe group',
                self.INPUT_LINES,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.INPUT_ALGORITHMS,
                self.tr('Algorithms'),
                options=list(self.ALGORITHMS),
                allowMultiple=True,
                optional=True
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
                self.INPUT_TEMPLATE,
                self.tr('PPNO template file'),
                extension='ext'
                )
            )

        # ADD A FILE DESTINATION FOR RESULTS
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output ppno file'),
                fileFilter='*.ext'
                )
            )
    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodes = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        pfield = self.parameterAsFields(parameters, self.FIELD_PRESSURE, context)
        pfield = pfield[0]
        links = self.parameterAsSource(parameters, self.INPUT_LINES, context)
        sfield = self.parameterAsFields(parameters, self.FIELD_SERIES, context)
        sfield = sfield[0]
        selected_algorithm_indexes = self.parameterAsEnums(parameters, self.INPUT_ALGORITHMS, context) or []
        selected_algorithms = [self.ALGORITHMS[index] for index in selected_algorithm_indexes]
        epanet_file = self.parameterAsFile(parameters, self.INPUT_EPANET, context)
        template_file = self.parameterAsFile(parameters, self.INPUT_TEMPLATE, context)

        # OUTPUT
        extfile = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # CHECK CRS
        if nodes.sourceCrs() != links.sourceCrs():
            error(feedback, "Layers have different CRS")
            return {}

        # TEMPLATE
        ppnof = parser.SectionedText()
        ppnof.read(template_file)

        required_sections = ('TITLE', 'INP', 'OPTIONS', 'PIPE_CATALOG', 'PRESSURES', 'PIPES')
        missing_sections = [section for section in required_sections if section not in ppnof.sections]
        if missing_sections:
            error(feedback, 'PPNO template missing sections: ' + ', '.join(missing_sections))
            return {}

        # TITLE SECTION
        msg = '; File generated automatically by Water Network Tools \n'
        ppnof.sections['TITLE'].append(msg)

        # INP SECTION
        ppnof.sections['INP'] = [epanet_file]

        # PIPE CATALOG SECTION
        catalog_lines = ppnof.sections['PIPE_CATALOG']
        if len(catalog_lines) != 1:
            error(feedback, 'PPNO template [PIPE_CATALOG] must contain exactly one file path')
            return {}

        catalog_source = self._resolve_template_path(template_file, catalog_lines[0])
        if not catalog_source.exists():
            error(feedback, 'PPNO pipe catalog file not found: ' + catalog_lines[0])
            return {}

        catalog_bytes = catalog_source.read_bytes()
        if self._catalog_has_section_header(catalog_bytes):
            error(feedback, 'PPNO pipe catalog must not contain section headers')
            return {}

        catalog_file = Path(extfile).with_suffix('.cat')
        catalog_file.write_bytes(catalog_bytes)
        ppnof.sections['PIPE_CATALOG'] = [catalog_file.name]
        # OPTIONS SECTION
        ppnof.sections['OPTIONS'] = self._options_with_algorithms(
            ppnof.sections['OPTIONS'],
            selected_algorithms
            )

        # PRESSURES SECTION
        ncnt = 0
        for feature in nodes.getFeatures():
            if feature[pfield]:
                ncnt += 1
                line = feature['id']+' '*4 + str(feature[pfield])
                ppnof.sections['PRESSURES'].append(line)

        # PIPES SECTION
        pcnt = 0
        for feature in links.getFeatures():
            if feature[sfield]:
                pcnt += 1
                line = (feature['id']+' '*4 + str(feature[sfield]))
                ppnof.sections['PIPES'].append(line)

        # WRITE EXT FILE
        ppnof.write(extfile)

        # SHOW INFO
        start(feedback, self.displayName())
        info(feedback, "Nodes with minimum pressure", ncnt)
        info(feedback, "Pipes to size", pcnt)
        info(feedback, "Pipe catalog file", catalog_file)
        info(feedback, "Output file", extfile)
        finish(feedback)
        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: extfile}




