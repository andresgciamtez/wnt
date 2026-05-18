"""Build network node and link layers from line features."""

from math import dist
from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsPointXY,
                       QgsFeatureRequest
                       )
from .base import WntProcessingAlgorithm
from ..utils import core as tools
from .messages import crs as log_crs
from .messages import error, finish, info
from .messages import start as log_start

class NetworkFromLinesAlgorithm(WntProcessingAlgorithm):
    """
    Built a network from lines.
    """

    # DEFINE CONSTANTS
    INPUT = 'INPUT'
    TOLERANCE = 'TOLERANCE'
    NODE_MASK = 'NODE_MASK'
    NODE_INI = 'NODE_INI'
    NODE_INC = 'NODE_INC'
    LINK_MASK = 'LINK_MASK'
    LINK_INI = 'LINK_INI'
    LINK_INC = 'LINK_INC'
    OUTPUT_NODES = 'OUTPUT_NODES'
    OUTPUT_LINES = 'OUTPUT_LINES'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return NetworkFromLinesAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'network_from_lines'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Network from lines'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return 'Build'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'build'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''<p>Builds EPANET-style network node and link layers from input line features.</p>
<ul>
<li>Line endpoints closer than the tolerance are merged into a single node.</li>
<li>The node layer contains <code>id</code>, <code>type</code>, and <code>elevation</code>.</li>
<li>The link layer contains <code>id</code>, <code>start</code>, <code>end</code>, <code>type</code>, and <code>length</code>.</li>
<li>Input layer fields are preserved in the output link layer.</li>
</ul>
<p>Limitations: multipart geometries and Z values are not supported. Looped lines are rejected.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Line vector layer input'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.TOLERANCE,
                self.tr('Minimum node separation, otherwise merge them'),
                defaultValue=0.001,
                minValue=0.0001,
                maxValue=1.0
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.NODE_MASK,
                self.tr('Node mask (P-$$-S generates P-01-S)'),
                defaultValue='$'
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_INI,
                self.tr('Number of the first node'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_INC,
                self.tr('Node increment'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.LINK_MASK,
                self.tr('Link mask (P-$$-S generates P-01-S)'),
                defaultValue='$'
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINK_INI,
                self.tr('Number of first link'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINK_INC,
                self.tr('Link increment'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )

        # ADD NODE AND LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('Network node layer')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                self.tr('Network link layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        linelayer = self.parameterAsSource(parameters, self.INPUT, context)
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        nmask = self.parameterAsString(parameters, self.NODE_MASK, context)
        nini = self.parameterAsInt(parameters, self.NODE_INI, context)
        ninc = self.parameterAsInt(parameters, self.NODE_INC, context)
        lmask = self.parameterAsString(parameters, self.LINK_MASK, context)
        lini = self.parameterAsInt(parameters, self.LINK_INI, context)
        linc = self.parameterAsInt(parameters, self.LINK_INC, context)

        # SEND INFORMATION TO THE USER
        log_start(feedback, self.displayName())
        log_crs(feedback, linelayer.sourceCrs())

        if linelayer.wkbType() == QgsWkbTypes.MultiLineString:
            error(feedback, "Source geometry is MultiLineString")
            return {}

        # READ LINESTRINGS (Geometry only pass)
        lines = []
        feedback.pushInfo("Reading input geometries...")
        request = QgsFeatureRequest().setNoAttributes()
        for feature in linelayer.getFeatures(request):
            geom = feature.geometry()
            polyline = geom.asPolyline()
            if len(polyline) < 2:
                error(feedback, f"Invalid LineString geometry (FID: {feature.id()})")
                return {}
            line = [(p.x(), p.y()) for p in polyline]

            if dist(line[0], line[-1]) < tol:
                error(feedback, f"Looped LineString detected (FID: {feature.id()})")
                return {}
            lines.append(line)

        info(feedback, "Input lines", len(lines))

        # CONFIG
        def n_format(index):
            return tools.format_id(nini + index*ninc, nmask)

        def l_format(index):
            return tools.format_id(lini + index*linc, lmask)

        # CALCULATE NETWORK
        nodes, links = tools.net_from_linestrings(lines, tol)

        # GENERATE NODE LAYER
        node_fields = QgsFields()
        node_fields.append(QgsField("id", QVariant.String))
        node_fields.append(QgsField("type", QVariant.String))
        node_fields.append(QgsField("elevation", QVariant.Double))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            node_fields,
            QgsWkbTypes.Point,
            linelayer.sourceCrs()
            )

        # ADD NODE FEATURES (Bulk)
        node_features = []
        for ncnt, (x, y) in enumerate(nodes):
            nodeid = n_format(ncnt)
            f = QgsFeature(node_fields)
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
            f.setAttributes([nodeid, '', 0.0])
            node_features.append(f)

            if len(node_features) >= 200:
                node_sink.addFeatures(node_features)
                node_features = []
                feedback.setProgress(25 * ncnt / len(nodes))

        if node_features:
            node_sink.addFeatures(node_features)

        # GENERATE LINK LAYER
        link_fields = QgsFields()
        link_fields.append(QgsField("id", QVariant.String))
        link_fields.append(QgsField("start", QVariant.String))
        link_fields.append(QgsField("end", QVariant.String))
        link_fields.append(QgsField("type", QVariant.String))
        link_fields.append(QgsField("length", QVariant.Double))
        link_fields.extend(linelayer.fields())
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            link_fields,
            QgsWkbTypes.LineString,
            linelayer.sourceCrs()
            )

        # ADD LINK FEATURES (Bulk)
        link_features = []
        # We need the attributes from the original features
        lcnt = 0
        for f_orig in linelayer.getFeatures():
            link = links[lcnt]
            linkid = l_format(lcnt)
            start_id = n_format(link[0])
            end_id = n_format(link[1])

            # Use points from the adjusted geometry (links[lcnt][2])
            poly = [QgsPointXY(x, y) for x, y in link[2]]
            length = tools.polyline_length(poly)

            attr = [linkid, start_id, end_id, 'PIPE', length]
            attr.extend(f_orig.attributes())

            g = QgsFeature(link_fields)
            g.setGeometry(QgsGeometry.fromPolylineXY(poly))
            g.setAttributes(attr)
            link_features.append(g)
            lcnt += 1

            if len(link_features) >= 200:
                link_sink.addFeatures(link_features)
                link_features = []
                feedback.setProgress(50 + 50 * lcnt / len(links))

        if link_features:
            link_sink.addFeatures(link_features)

        info(feedback, "Output nodes", len(nodes))
        info(feedback, "Output links", len(links))
        finish(feedback)

        if feedback.isCanceled():
            return {}

        return {self.OUTPUT_NODES: node_id, self.OUTPUT_LINES: link_id}
