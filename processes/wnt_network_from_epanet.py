"""Import network layers from an EPANET input file."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterCrs,
                       QgsGeometry,
                       QgsWkbTypes
                       )
from .base import WntProcessingAlgorithm
from ..utils import utils_core as tools
from .messages import crs as log_crs
from .messages import finish, info, start

class NetworkFromEpanetAlgorithm(WntProcessingAlgorithm):
    """
    Built a network from an EPANET file.
    """

    # DEFINE CONSTANTS

    INPUT = 'INPUT'
    OUTPUT_NODES = 'OUTPUT_NODES'
    OUTPUT_LINES = 'OUTPUT_LINES'
    CRS = 'CRS'


    def createInstance(self):
        """
        createInstance must return a new copy of algorithm.
        """
        return NetworkFromEpanetAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'network_from_epanet'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Network from EPANET file'

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
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''<p>Imports an EPANET <code>.inp</code> file and creates node and link layers.</p>
<ul>
<li>Node attributes: <code>id</code>, <code>type</code>, <code>elevation</code>.</li>
<li>Link attributes: <code>id</code>, <code>start</code>, <code>end</code>, <code>type</code>, <code>length</code>, <code>diameter</code>, <code>roughness</code>.</li>
<li>Supported node sections: <code>JUNCTIONS</code>, <code>RESERVOIRS</code>, <code>TANKS</code>.</li>
<li>Supported link sections: <code>PIPES</code>, <code>PUMPS</code>, <code>VALVES</code>.</li>
</ul>
        ''')

    def initAlgorithm(self, config=None):
        """
         Define the inputs and outputs of the algorithm.
        """

        # ADD INPUT FILE AND CRS SELECTOR
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('EPANET file'),
                extension='inp'
                )
            )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                self.tr('Coordinate reference system (CRS)')
                )
            )
        # ADD NODE AND LINK SINKS
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('EPANET nodes')
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                self.tr('EPANET links'),
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        epanetf = self.parameterAsFile(parameters, self.INPUT, context)
        crs = self.parameterAsCrs(parameters, self.CRS, context)

        # SHOW INFO
        start(feedback, self.displayName())
        log_crs(feedback, crs)

        # READ NETWORK
        network = tools.WntNetwork()
        network.from_epanet(epanetf)
        nodes = network.nodes()
        links = network.links()

        # GENERATE NODES LAYER
        newfields = QgsFields()
        newfields.append(QgsField("id", QMetaType.QString))
        newfields.append(QgsField("type", QMetaType.QString))
        newfields.append(QgsField("elevation", QMetaType.Double))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields,
            QgsWkbTypes.Point,
            crs
            )

        # ADD NODES
        ncnt = 0
        ntot = len(nodes)
        for node in nodes:
            #add feature to sink
            ncnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(node.to_wkt()))
            f.setAttributes([node.name(), node.get_type(), node.get_elevation()])

            # ADD NODE
            node_sink.addFeature(f)

            # SHOW PROGRESS
            if ntot > 0 and ncnt % 100 == 0:
                feedback.setProgress(50*ncnt/ntot) # Update the progress bar

        # GENERATE LINKS LAYER
        newfields = QgsFields()
        newfields.append(QgsField("id", QMetaType.QString))
        newfields.append(QgsField("start", QMetaType.QString))
        newfields.append(QgsField("end", QMetaType.QString))
        newfields.append(QgsField("type", QMetaType.QString))
        newfields.append(QgsField("length", QMetaType.Double))
        newfields.append(QgsField("diameter", QMetaType.Double))
        newfields.append(QgsField("roughness", QMetaType.Double))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs
            )

        # ADD LINKS
        lcnt = 0
        ltot = len(links)
        for link in links:
            lcnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(link.to_wkt()))
            if link.get_type() in ['PIPE', 'CVPIPE']:
                f.setAttributes([link.name(),
                                link.start(),
                                link.end(),
                                link.get_type(),
                                link.epanet['length'],
                                link.epanet['diameter'],
                                link.epanet['roughness']]
                                )
            else:
                f.setAttributes(
                    [link.name(),
                     link.start(),
                     link.end(),
                     link.get_type(),
                     None,
                     None,
                     None]
                    )

            # ADD LINK
            link_sink.addFeature(f)

            # SHOW PROGRESS
            if ltot > 0 and lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/ltot) # Update the progress bar

        # SHOW INFO
        info(feedback, "Input file", epanetf)
        info(feedback, "Nodes imported", ncnt)
        info(feedback, "Links imported", lcnt)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_NODES: node_id, self.OUTPUT_LINES: link_id}

