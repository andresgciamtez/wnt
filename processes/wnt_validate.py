"""Validate basic network topology."""

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsField,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource

                       )
from .base import WntProcessingAlgorithm
from ..utils import core as tools
from .messages import finish, info, message, start

class ValidateAlgorithm(WntProcessingAlgorithm):
    """
    Validate a network.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    INPUT_LINES = 'INPUT_LINES'
    OUTPUT_NODES = 'OUTPUT_NODES'
    OUTPUT_LINES = 'OUTPUT_LINES'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ValidateAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'validate'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Validate'

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
        return self.tr('''<p>Analyses the network graph and reports topology problems.</p>
<ul>
<li>Orphan nodes.</li>
<li>Duplicate nodes.</li>
<li>Links with undefined endpoints.</li>
<li>Duplicate links.</li>
<li>Loops, where start and end node are the same.</li>
</ul>
<p>Detected problems are written to the <code>problems</code> field.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NODES,
                self.tr('Input nodes layer'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
                self.tr('Input links layer'),
                [QgsProcessing.TypeVectorLine]
                )
            )

        # ADD NODE AND LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('Audited node layer')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                self.tr('Audited Link layer')
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
        newfields.append(QgsField("problems", QVariant.String))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields,
            QgsWkbTypes.Point,
            nodelay.sourceCrs()
            )
        newfields = linklay.fields()
        newfields.append(QgsField("problems", QVariant.String))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields,
            QgsWkbTypes.LineString,
            linklay.sourceCrs()
            )

        # DEFINE NETWORK
        net = tools.WntNetwork()

        # LOAD NODES
        ncnt = 0
        for f in nodelay.getFeatures():
            ncnt += 1
            net.add_node(tools.WntNode(f['id']))

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(25*ncnt/nodelay.featureCount())

        # lOAD LINKS
        lcnt = 0
        for f in linklay.getFeatures():
            lcnt += 1
            net.add_link(tools.WntLink(f['id'], f['start'], f['end']))

            # SHOW POROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(25+25*lcnt/linklay.featureCount())

        # VALIDATE
        problems = net.validate()

        # WRITE OUTPUT
        start(feedback, self.displayName())

        # WRITE NODE PROBLEMS
        ncnt = 0
        for f in nodelay.getFeatures():
            ncnt += 1
            msg = ''

            # ORPHAN NODE
            if f['id'] in problems['orphan nodes']:
                msg = 'Orphan.'

            # DUPLICATED NODE ID
            if f['id'] in problems['duplicate nodes']:
                msg += ' ' if msg else ''
                msg += 'Duplicated.'

            # ADD FEATURE
            attrib = f.attributes()
            attrib.extend([msg])
            f.setAttributes(attrib)
            node_sink.addFeature(f)

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(50+25*ncnt/nodelay.featureCount())

        # WRITE LINK PROBLEMS
        lcnt = 0
        for f in linklay.getFeatures():
            lcnt += 1
            msg = ''

            # UNDEFINED START OR END
            if f['id'] in problems['undefined node links']:
                msg = 'Undefined node links.'

            # DUPLICATED ID
            if f['id'] in problems['duplicate links']:
                msg += ' ' if msg else ''
                msg += 'Duplicate link.'

            # LOOP. START NODE ID = END NODE ID
            if f['id'] in problems['loops']:
                msg += ' ' if msg else ''
                msg += 'Loop.'

            # ADD FEATURE
            attrib = f.attributes()
            attrib.extend([msg])
            f.setAttributes(attrib)
            link_sink.addFeature(f)

            # SHOW PROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(75+25*lcnt/linklay.featureCount())

        # SHOW INFO
        info(feedback, "Input nodes", ncnt)
        info(feedback, "Input links", lcnt)
        pcnt = 0
        for k, v in problems.items():
            pcnt += len(v)
            info(feedback, k.title(), len(v))

        if pcnt:
            msg = '{} problems detected. Check the network.'.format(pcnt)
        else:
            msg = "Network is valid."
        message(feedback, msg)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_NODES: node_id, self.OUTPUT_LINES: link_id}

