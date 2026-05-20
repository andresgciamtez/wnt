"""Classify network links into branched and meshed areas."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsField,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsWkbTypes
                       )
from .base import WntProcessingAlgorithm
from ..utils import utils_graph as gr
from .messages import finish, info, start

class ClassifyAlgorithm(WntProcessingAlgorithm):
    """
    Build an epanet model file from node and link layers.
    """

    # DEFINE CONSTANTS
    INPUT_LINES = 'INPUT_LINES'
    OUTPUT_LINES = 'OUTPUT_LINES'



    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ClassifyAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'classify'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Classify'

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return 'Graph'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'graph'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''<p>Classifies network links into branched and meshed areas.</p>
<ul>
<li>Adds <code>graph_type</code>: <code>BRANCHED</code> or <code>MESHED</code>.</li>
<li>Adds <code>sub</code>: subnetwork identifier.</li>
</ul>
<p>Use this algorithm to support network sectorization.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT NETWORK LINKS
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
                self.tr('Network links layer input'),
                [QgsProcessing.TypeVectorLine]
                )
            )

        # ADD LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                self.tr('Subnetwork link layer')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        links = self.parameterAsSource(parameters, self.INPUT_LINES, context)

        # OUTPUT
        newfields = links.fields()
        newfields.append(QgsField("graph_type", QMetaType.QString))
        newfields.append(QgsField("sub", QMetaType.Int))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs=links.sourceCrs()
            )

        # CREATE NETWORK
        netg = gr.Graph()

        # READ NETWORK
        nofl = links.featureCount()

        # LINKS
        cnt = 0
        for f in links.getFeatures():
            netg.add_edge(f['id'], f['start'], f['end'])

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(25*cnt/nofl)

        # GENERATE SUBNETWORKS
        classified = netg.classify()

        # WRITE LINK LAYER
        cnt = 0
        for f in links.getFeatures():
            cnt += 1
            attr = f.attributes()
            attr.extend(list(classified[f['id']][:]))
            f.setAttributes(attr)
            link_sink.addFeature(f)

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(75+25*cnt/nofl)


        # SHOW INFO
        start(feedback, self.displayName())
        info(feedback, "Input links", nofl)
        info(feedback, "Classified links", cnt)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_LINES: link_id}

