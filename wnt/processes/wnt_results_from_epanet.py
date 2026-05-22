"""Import hydraulic results from EPANET toolkit runs."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
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
    OUTPUT_NODES = 'OUTPUT_NODES'
    OUTPUT_LINES = 'OUTPUT_LINES'

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
        return self.tr('''<p>Imports hydraulic results from an EPANET simulation.</p>
<ul>
<li>Node results: <code>time</code>, <code>demand</code>, <code>head</code>, <code>pressure</code>.</li>
<li>Link results: <code>time</code>, <code>flow</code>, <code>velocity</code>, <code>headloss</code>, <code>status</code>, <code>setting</code>, <code>energy</code>.</li>
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

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        epanet_file = self.parameterAsFile(parameters, self.INPUT, context)

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
        newfields = QgsFields()
        newfields.append(QgsField("time", QMetaType.QTime))
        newfields.append(QgsField("id", QMetaType.QString, len=max_label_len))
        newfields.append(QgsField("demand", QMetaType.Double))
        newfields.append(QgsField("head", QMetaType.Double))
        newfields.append(QgsField("pressure", QMetaType.Double))
        (node_sink, nodes_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields
            )

        # DEFINE LINK LAYER
        newfields = QgsFields()
        newfields.append(QgsField("time", QMetaType.QTime))
        newfields.append(QgsField("id", QMetaType.QString, len=max_label_len))
        newfields.append(QgsField("flow", QMetaType.Double))
        newfields.append(QgsField("velocity", QMetaType.Double))
        newfields.append(QgsField("headloss", QMetaType.Double))
        newfields.append(QgsField("status", QMetaType.QString, len=6))
        newfields.append(QgsField("setting", QMetaType.Double))
        newfields.append(QgsField("energy", QMetaType.Double))
        (link_sink, links_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields
            )

        # SHOW TOOLKIT INFORMATION
        info(feedback, "EPANET toolkit library", toolkit_info.library_path)
        info(feedback, "Platform", f"{toolkit_info.platform} {toolkit_info.architecture}")
        info(feedback, "EPANET toolkit version", toolkit_info.version)
        info(feedback, "EPANET toolkit API", toolkit_info.api)
        info(feedback, "Input file", epanet_file)

        # GET AND WRITE RESULTS
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

        # SHOW NODES AND LINKS PROCESSED
        message(feedback, "Results loaded successfully")
        info(feedback, "Hydraulic time steps", results.step_count)
        info(feedback, "Nodes", results.node_count)
        info(feedback, "Links", results.link_count)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_NODES: nodes_id, self.OUTPUT_LINES: links_id}
