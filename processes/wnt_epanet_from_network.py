"""Export a network layer pair to an EPANET input file."""

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from .base import WntProcessingAlgorithm
from ..utils import utils_core as tools
from .messages import crs as log_crs
from .messages import error, finish, info, start

class EpanetFromNetworkAlgorithm(WntProcessingAlgorithm):
    """
    Build an EPANET model file from node and link layers.
    """

    # DEFINE CONSTANTS

    INPUT_NODES = 'INPUT_NODES'
    INPUT_LINES = 'INPUT_LINES'
    INPUT_TEMPLATE = 'INPUT_TEMPLATE'
    OUTPUT = 'OUTPUT'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return EpanetFromNetworkAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'epanet_from_network'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'EPANET file from network'

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
        return self.tr('''<p>Creates an EPANET <code>.inp</code> file from network node and link layers and an EPANET template.</p>
<ul>
<li>Adds nodes to <code>JUNCTIONS</code>, <code>RESERVOIRS</code>, or <code>TANKS</code>.</li>
<li>Adds links to <code>PIPES</code>, <code>PUMPS</code>, or <code>VALVES</code>.</li>
<li>Exports coordinates and intermediate vertices.</li>
<li>Pipe diameter and roughness are not exported; add them using scenario files.</li>
</ul>
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
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_TEMPLATE,
                self.tr('EPANET template file'),
                extension='inp'
                )
            )

        # ADD A FILE DESTINATION
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('EPANET model file'),
                fileFilter='*.inp'
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        nodes = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        links = self.parameterAsSource(parameters, self.INPUT_LINES, context)
        template = self.parameterAsFile(parameters, self.INPUT_TEMPLATE, context)

        # CHECK CRS
        crs = nodes.sourceCrs()
        if crs == links.sourceCrs():

            # SEND INFORMATION TO THE USER
            start(feedback, self.displayName())
            log_crs(feedback, crs)
        else:
            error(feedback, "Layers have different CRS")
            return {}

        # OUTPUT
        EPANET = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # BUILD NETWORK
        newnet = tools.WntNetwork()

        # NODES
        ncnt = 0
        for f in nodes.getFeatures():
            ncnt += 1
            newnode = tools.WntNode(f['id'])
            newnode.from_wkt(f.geometry().asWkt())
            newnode.set_type(f['type'])
            newnode.set_elevation(f['elevation'])
            newnet.add_node(newnode)

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(50*ncnt/nodes.featureCount())

        # LINKS
        lcnt = 0
        for f in links.getFeatures():
            lcnt += 1
            newlink = tools.WntLink(f['id'], f['start'], f['end'])
            newlink.from_wkt(f.geometry().asWkt())
            newlink.epanet['length'] = f['length']
            newlink.set_type(f['type'])
            newnet.add_link(newlink)

            # SHOW POROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/links.featureCount())

        # WRITE NET
        newnet.to_epanet(EPANET, template)
        EPANET = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # SHOW INFO
        info(feedback, "Nodes exported", ncnt)
        info(feedback, "Links exported", lcnt)
        info(feedback, "Output file", EPANET)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: EPANET}

