"""Import hydraulic results from EPANET toolkit runs."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFile)
from .base import WntProcessingAlgorithm
from .messages import error, finish, info, message, start
from ..utils.utils_epanet_api import (
    EpanetConfigurationError,
    EpanetError,
    EpanetToolkit,
)


class ResultsFromEpanetAlgorithm(WntProcessingAlgorithm):
    """
    Import EPANET result from EPANET toolkit.
    """

    # DEFINE CONSTANTS
    INPUT = 'INPUT'
    RESULT_TYPE = 'RESULT_TYPE'
    OUTPUT_NODES = 'OUTPUT_NODES'
    OUTPUT_LINES = 'OUTPUT_LINES'
    OUTPUT_NODE_QUALITY = 'OUTPUT_NODE_QUALITY'
    OUTPUT_LINK_QUALITY = 'OUTPUT_LINK_QUALITY'
    RESULT_HYDRAULIC = 0
    RESULT_QUALITY = 1
    RESULT_BOTH = 2
    RESULT_OPTIONS = (
        'Hydraulic results',
        'Quality results',
        'Hydraulic and quality results',
    )

    def createInstance(self):
        """
        createInstance must return a new copy of algorithm.
        """
        return ResultsFromEpanetAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'results_from_epanet'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Results from EPANET'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return 'Import'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'import'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''<p>Imports hydraulic and quality results from an EPANET simulation.</p>
<ul>
<li>Node results: <code>time</code>, <code>demand</code>, <code>head</code>, <code>pressure</code>.</li>
<li>Link results: <code>time</code>, <code>flow</code>, <code>velocity</code>, <code>headloss</code>, <code>status</code>, <code>setting</code>, <code>energy</code>.</li>
<li>Quality results: <code>time</code>, <code>id</code>, <code>quality</code>.</li>
</ul>
<p>Configure the EPANET toolkit library before running this algorithm.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
         Define the inputs and outputs of the algorithm.
        """

        # ADD INPUT FILE
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('EPANET file'),
                extension='inp'
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.RESULT_TYPE,
                self.tr('Result type'),
                options=[self.tr(option) for option in self.RESULT_OPTIONS],
                defaultValue=self.RESULT_HYDRAULIC,
                optional=False
            )
        )

        # ADD NODE AND LINK SINKS
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('Node results')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                self.tr('Link results'),
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODE_QUALITY,
                self.tr('Node quality results'),
                optional=True
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINK_QUALITY,
                self.tr('Link quality results'),
                optional=True
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        epanet_file = self.parameterAsFile(parameters, self.INPUT, context)
        result_type = self.parameterAsEnum(parameters, self.RESULT_TYPE, context)
        include_hydraulic = result_type in (self.RESULT_HYDRAULIC, self.RESULT_BOTH)
        include_quality = result_type in (self.RESULT_QUALITY, self.RESULT_BOTH)

        start(feedback, self.displayName())

        # LOAD EPANET TOOLKIT
        try:
            toolkit = EpanetToolkit.from_config()
            toolkit_info = toolkit.info()
            max_label_len = toolkit.constants.max_label_len
        except EpanetConfigurationError as exc:
            error(feedback, str(exc))
            return {}
        except EpanetError as exc:
            error(feedback, exc.message)
            return {}

        # DEFINE NODE LAYER
        newfields = self._hydraulic_node_fields(max_label_len)
        (node_sink, nodes_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields
            )

        # DEFINE LINK LAYER
        newfields = self._hydraulic_link_fields(max_label_len)
        (link_sink, links_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields
            )
        quality_fields = self._quality_fields(max_label_len)
        (node_quality_sink, node_quality_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODE_QUALITY,
            context,
            quality_fields
            )
        (link_quality_sink, link_quality_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINK_QUALITY,
            context,
            quality_fields
            )

        # SHOW TOOLKIT INFORMATION
        info(feedback, "EPANET toolkit library", toolkit_info.library_path)
        info(feedback, "Platform", f"{toolkit_info.platform} {toolkit_info.architecture}")
        info(feedback, "EPANET toolkit version", toolkit_info.version)
        info(feedback, "EPANET toolkit API", toolkit_info.api)
        info(feedback, "Input file", epanet_file)

        result_map = {}
        if include_hydraulic:
            try:
                results = toolkit.read_hydraulic_results(epanet_file)
            except EpanetError as exc:
                error(feedback, exc.message)
                return {}

            for node_result in results.node_rows:
                f = QgsFeature()
                f.setAttributes(node_result)
                node_sink.addFeature(f)

            for link_result in results.link_rows:
                f = QgsFeature()
                f.setAttributes(link_result)
                link_sink.addFeature(f)
            result_map[self.OUTPUT_NODES] = nodes_id
            result_map[self.OUTPUT_LINES] = links_id
            info(feedback, "Hydraulic time steps", results.step_count)
            info(feedback, "Nodes", results.node_count)
            info(feedback, "Links", results.link_count)

        if include_quality:
            try:
                quality_results = toolkit.read_quality_results(epanet_file)
            except EpanetConfigurationError as exc:
                error(feedback, str(exc))
                return {}
            except EpanetError as exc:
                error(feedback, exc.message)
                return {}

            for node_result in quality_results.node_rows:
                f = QgsFeature()
                f.setAttributes(node_result)
                node_quality_sink.addFeature(f)

            for link_result in quality_results.link_rows:
                f = QgsFeature()
                f.setAttributes(link_result)
                link_quality_sink.addFeature(f)
            result_map[self.OUTPUT_NODE_QUALITY] = node_quality_id
            result_map[self.OUTPUT_LINK_QUALITY] = link_quality_id
            info(feedback, "Quality time steps", quality_results.step_count)
            info(feedback, "Quality nodes", quality_results.node_count)
            info(feedback, "Quality links", quality_results.link_count)

        # SHOW NODES AND LINKS PROCESSED
        message(feedback, "Results loaded successfully")
        info(feedback, "Result type", self.RESULT_OPTIONS[result_type])
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return result_map

    @staticmethod
    def _hydraulic_node_fields(max_label_len):
        fields = QgsFields()
        fields.append(QgsField("time", QMetaType.QTime))
        fields.append(QgsField("id", QMetaType.QString, len=max_label_len))
        fields.append(QgsField("demand", QMetaType.Double))
        fields.append(QgsField("head", QMetaType.Double))
        fields.append(QgsField("pressure", QMetaType.Double))
        return fields

    @staticmethod
    def _hydraulic_link_fields(max_label_len):
        fields = QgsFields()
        fields.append(QgsField("time", QMetaType.QTime))
        fields.append(QgsField("id", QMetaType.QString, len=max_label_len))
        fields.append(QgsField("flow", QMetaType.Double))
        fields.append(QgsField("velocity", QMetaType.Double))
        fields.append(QgsField("headloss", QMetaType.Double))
        fields.append(QgsField("status", QMetaType.QString, len=6))
        fields.append(QgsField("setting", QMetaType.Double))
        fields.append(QgsField("energy", QMetaType.Double))
        return fields

    @staticmethod
    def _quality_fields(max_label_len):
        fields = QgsFields()
        fields.append(QgsField("time", QMetaType.QTime))
        fields.append(QgsField("id", QMetaType.QString, len=max_label_len))
        fields.append(QgsField("quality", QMetaType.Double))
        return fields
