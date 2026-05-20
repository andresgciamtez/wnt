"""Calculate node degrees for a network graph."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsField,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsWkbTypes
                       )
from .base import WntProcessingAlgorithm
from ..utils import graph
from .messages import finish, info, start

class NodeDegreesAlgorithm(WntProcessingAlgorithm):
    """
    Build an epanet model file from node and link layers.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    INPUT_LINES = 'INPUT_LINES'
    OUTPUT_NODES = 'OUTPUT_NODES'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return NodeDegreesAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'node_degrees'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Node degrees'

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
        return self.tr('''<p>Calculates the graph degree of each network node.</p>
<ul>
<li>The degree is the number of links connected to a node.</li>
<li>Orphan nodes have degree <code>0</code>.</li>
<li>Leaf nodes have degree <code>1</code>.</li>
<li>Continuity nodes have degree <code>2</code>.</li>
</ul>
<p>Results are written to the <code>degree</code> field.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT NETWORK (NODES AND LINKS)
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NODES,
                self.tr('Network node layer input'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
                self.tr('Network links layer input'),
                [QgsProcessing.TypeVectorLine]
                )
            )

        # ADD NODE AND LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('Node degree layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        nodelay = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        linklay = self.parameterAsSource(parameters, self.INPUT_LINES, context)

        # OUTPUT
        newfields = nodelay.fields()
        degree_idx = newfields.lookupField('degree')
        if degree_idx < 0:
            newfields.append(QgsField('degree', QMetaType.Int))
            degree_idx = newfields.lookupField('degree')
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields,
            QgsWkbTypes.Point,
            nodelay.sourceCrs()
            )

        # LOAD LAYERS
        nofn = nodelay.featureCount()
        nofl = linklay.featureCount()

        # ADD NODES
        node_ids = []
        cnt = 0
        for f in nodelay.getFeatures():
            cnt += 1
            node_ids.append(f['id'])

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(33*cnt/nofn)

        # ADD LINKS
        links = []
        cnt = 0
        for f in linklay.getFeatures():
            cnt += 1
            links.append((f['id'], f['start'], f['end']))

            # SHOW POROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(33+33*cnt/nofl)

        # CALCULATE DEGREES
        degrees = graph.node_degrees_from_records(node_ids, links)

        # WRITE NODE DEGREES
        cnt = 0
        for f in nodelay.getFeatures():
            cnt += 1
            attr = f.attributes()
            if len(attr) < len(newfields):
                attr.extend([None] * (len(newfields) - len(attr)))
            attr[degree_idx] = degrees[f['id']]
            f.setAttributes(attr)
            node_sink.addFeature(f)

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(67+33*cnt/nofn)

        # SHOW INFO
        start(feedback, self.displayName())
        info(feedback, "Input nodes", nofn)
        info(feedback, "Input links", nofl)
        info(feedback, "Output nodes", nofn)
        info(feedback, "Minimum degree", min(degrees.values()))
        info(feedback, "Maximum degree", max(degrees.values()))
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_NODES: node_id}

