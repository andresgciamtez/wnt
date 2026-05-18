"""Import network layers from a LandXML pipe network."""

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsLineString,
                       QgsPoint,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsGeometry,
                       QgsWkbTypes
                       )
from .base import WntProcessingAlgorithm
from ..utils import landxml
from .messages import crs as log_crs
from .messages import finish, info, start

class NetworkFromLandXMLAlgorithm(WntProcessingAlgorithm):
    """
    Built a network from an epanet file.
    """

    # DEFINE CONSTANTS

    INPUT = 'INPUT'
    OUTPUT_NODES = 'OUTPUT_NODES'
    OUTPUT_LINES = 'OUTPUT_LINES'


    def createInstance(self):
        """
        createInstance must return a new copy of algorithm.
        """
        return NetworkFromLandXMLAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'network_from_landxml'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Network from LandXML file'

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
        return self.tr('''<p>Imports pipe networks from a LandXML 1.2 file.</p>
<ul>
<li>Creates node and link layers from the LandXML pipe network definitions.</li>
<li>Uses the CRS information stored in the LandXML file when available.</li>
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
                self.tr('LandXML file'),
                extension='xml'
                )
            )

        # ADD NODE AND LINK SINKS
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('Nodes')
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                self.tr('Links'),
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # READ NETWORK
        landxmlfn = self.parameterAsFile(parameters, self.INPUT, context)
        imp_net = landxml.network_from_xml(landxmlfn)
        networks = imp_net['networks']
        if 'epsg_code' in imp_net:
            crs = QgsCoordinateReferenceSystem('EPSG:' + imp_net['epsg_code'])
        else:
            crs = QgsCoordinateReferenceSystem('WKT:' + imp_net['wkt_crs'])

        # SHOW INFO
        start(feedback, self.displayName())
        log_crs(feedback, crs)

        # GENERATE SINK LAYER
        newfields = QgsFields()
        newfields.append(QgsField("network", QVariant.String))
        newfields.append(QgsField("network_type", QVariant.String))
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("elev_sump", QVariant.Double))
        newfields.append(QgsField("elev_rim", QVariant.Double))
        newfields.append(QgsField("depth", QVariant.Double))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields,
            QgsWkbTypes.Point,
            crs
            )

        newfields = QgsFields()
        newfields.append(QgsField("network", QVariant.String))
        newfields.append(QgsField("network_type", QVariant.String))
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("start", QVariant.String))
        newfields.append(QgsField("end", QVariant.String))
        newfields.append(QgsField("start_elv", QVariant.Double))
        newfields.append(QgsField("start_offset", QVariant.Double))
        newfields.append(QgsField("start_depth", QVariant.Double))
        newfields.append(QgsField("end_elv", QVariant.Double))
        newfields.append(QgsField("end_offset", QVariant.Double))
        newfields.append(QgsField("end_depth", QVariant.Double))
        newfields.append(QgsField("length", QVariant.Double))
        newfields.append(QgsField("slope", QVariant.Double))
        newfields.append(QgsField("sect_type", QVariant.String))
        newfields.append(QgsField("section", QVariant.String))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs
            )

        netcnt = nodcnt = lnkcnt = 0
        # ADD NETWORK
        for netname, network in networks.items():
            netcnt += 1
            net_type = network['net_type']
            # ADD NODES
            for nodename, node in network['nodes'].items():
                nodcnt += 1
                f = QgsFeature()
                point = QgsPoint(node['x'], node['y'])
                f.setGeometry(point)
                f.setAttributes([netname,
                                 net_type,
                                 nodename,
                                 node['elev_sump'],
                                 node['elev_rim'],
                                 node['depth']
                                 ])
                node_sink.addFeature(f)

            # ADD LINKS
            for linkname, link in network['links'].items():
                lnkcnt += 1
                g = QgsFeature()
                x = network['nodes'][link['start']]['x']
                y = network['nodes'][link['start']]['y']
                spoint = QgsPoint(x, y)
                x = network['nodes'][link['end']]['x']
                y = network['nodes'][link['end']]['y']
                epoint = QgsPoint(x, y)
                g.setGeometry(QgsGeometry(QgsLineString([spoint, epoint])))
                g.setAttributes([netname,
                                 net_type,
                                 linkname,
                                 link['start'],
                                 link['end'],
                                 link['start_elev'],
                                 link['start_offset'],
                                 link['start_depth'],
                                 link['end_elev'],
                                 link['end_offset'],
                                 link['end_depth'],
                                 link['length'],
                                 link['slope'],
                                 link['sect_type'],
                                 link['section']
                                 ])
                link_sink.addFeature(g)

        # SHOW PROGRESS
        feedback.setProgress(100) # Update the progress bar

        # SHOW INFO
        info(feedback, "Input file", landxmlfn)
        info(feedback, "Networks imported", netcnt)
        info(feedback, "Nodes imported", nodcnt)
        info(feedback, "Links imported", lnkcnt)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_NODES: node_id, self.OUTPUT_LINES: link_id}

