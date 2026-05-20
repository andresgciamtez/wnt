"""Build network node and link layers from line features."""

from collections import defaultdict
from math import dist, isfinite
from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsPointXY
                       )
from .base import WntProcessingAlgorithm
from ..utils import utils_core as tools
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
    MASK_NODE = 'MASK_NODE'
    INITIAL_NODE = 'INITIAL_NODE'
    INCREMENT_NODE = 'INCREMENT_NODE'
    MASK_LINK = 'MASK_LINK'
    INITIAL_LINK = 'INITIAL_LINK'
    INCREMENT_LINK = 'INCREMENT_LINK'
    USE_LINE_ELEVATION = 'USE_LINE_ELEVATION'
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
<li>Multipart geometries are split into individual output links.</li>
<li>When enabled, line endpoint Z values are copied to nodes and checked against the merge tolerance.</li>
</ul>
<p>Looped lines are rejected.</p>
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
                self.MASK_NODE,
                self.tr('Node mask (P-$$-S generates P-01-S)'),
                defaultValue='$'
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INITIAL_NODE,
                self.tr('Number of the first node'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INCREMENT_NODE,
                self.tr('Node increment'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.MASK_LINK,
                self.tr('Link mask (P-$$-S generates P-01-S)'),
                defaultValue='$'
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INITIAL_LINK,
                self.tr('Number of first link'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.INCREMENT_LINK,
                self.tr('Link increment'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.USE_LINE_ELEVATION,
                self.tr('Use line endpoint Z values as node elevations'),
                defaultValue=False
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
        nmask = self.parameterAsString(parameters, self.MASK_NODE, context)
        nini = self.parameterAsInt(parameters, self.INITIAL_NODE, context)
        ninc = self.parameterAsInt(parameters, self.INCREMENT_NODE, context)
        lmask = self.parameterAsString(parameters, self.MASK_LINK, context)
        lini = self.parameterAsInt(parameters, self.INITIAL_LINK, context)
        linc = self.parameterAsInt(parameters, self.INCREMENT_LINK, context)
        use_line_elevation = self.parameterAsBool(parameters, self.USE_LINE_ELEVATION, context)

        # SEND INFORMATION TO THE USER
        log_start(feedback, self.displayName())
        log_crs(feedback, linelayer.sourceCrs())

        # READ LINESTRINGS
        lines = []
        line_attrs = []
        line_elevations = []
        feedback.pushInfo("Reading input geometries...")
        for feature in linelayer.getFeatures():
            geom = feature.geometry()
            for line in self._line_parts(geom):
                if len(line) < 2:
                    error(feedback, f"Invalid LineString geometry (FID: {feature.id()})")
                    return {}

                start = tools.xy(line[0])
                end = tools.xy(line[-1])
                if dist(start, end) < tol:
                    error(feedback, f"Looped LineString detected (FID: {feature.id()})")
                    return {}

                lines.append(line)
                line_attrs.append(feature.attributes())
                line_elevations.append((self._point_z(line[0]), self._point_z(line[-1])))

        info(feedback, "Input lines", len(lines))

        # CONFIG
        def n_format(index):
            return tools.format_id(nini + index*ninc, nmask)

        def l_format(index):
            return tools.format_id(lini + index*linc, lmask)

        # CALCULATE NETWORK
        nodes, links = tools.net_from_linestrings(lines, tol)
        node_elevations = self._node_elevations(links, line_elevations, tol) if use_line_elevation else {}
        if node_elevations is None:
            error(feedback, "Line endpoint elevations merged into a node differ more than tolerance")
            return {}

        # GENERATE NODE LAYER
        node_fields = QgsFields()
        node_fields.append(QgsField("id", QMetaType.QString))
        node_fields.append(QgsField("type", QMetaType.QString))
        node_fields.append(QgsField("elevation", QMetaType.Double))
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
            elevation = node_elevations.get(ncnt, 0.0)
            f = QgsFeature(node_fields)
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
            f.setAttributes([nodeid, '', elevation])
            node_features.append(f)

            if len(node_features) >= 200:
                node_sink.addFeatures(node_features)
                node_features = []
                feedback.setProgress(25 * ncnt / len(nodes))

        if node_features:
            node_sink.addFeatures(node_features)

        # GENERATE LINK LAYER
        link_fields = QgsFields()
        link_fields.append(QgsField("id", QMetaType.QString))
        link_fields.append(QgsField("start", QMetaType.QString))
        link_fields.append(QgsField("end", QMetaType.QString))
        link_fields.append(QgsField("type", QMetaType.QString))
        link_fields.append(QgsField("length", QMetaType.Double))
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
        for lcnt, link in enumerate(links):
            linkid = l_format(lcnt)
            start_id = n_format(link[0])
            end_id = n_format(link[1])

            # Use points from the adjusted geometry (links[lcnt][2])
            poly = [QgsPointXY(x, y) for x, y in link[2]]
            length = tools.polyline_length(poly)

            attr = [linkid, start_id, end_id, 'PIPE', length]
            attr.extend(line_attrs[lcnt])

            g = QgsFeature(link_fields)
            g.setGeometry(QgsGeometry.fromPolylineXY(poly))
            g.setAttributes(attr)
            link_features.append(g)
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

    @staticmethod
    def _line_parts(geometry):
        """Return single-part QGIS polylines from a line or multiline geometry."""
        if hasattr(geometry, 'constGet'):
            geometry_object = geometry.constGet()
            if hasattr(geometry_object, 'numGeometries'):
                return [
                    NetworkFromLinesAlgorithm._points_from_line(geometry_object.geometryN(index))
                    for index in range(geometry_object.numGeometries())
                ]
            return [NetworkFromLinesAlgorithm._points_from_line(geometry_object)]

        if hasattr(geometry, 'asMultiPolyline'):
            lines = geometry.asMultiPolyline()
            if lines:
                return lines
        return [geometry.asPolyline()]

    @staticmethod
    def _points_from_line(line):
        """Return QGIS points from a core line geometry."""
        if hasattr(line, 'numPoints') and hasattr(line, 'pointN'):
            return [line.pointN(index) for index in range(line.numPoints())]
        return list(line)

    @staticmethod
    def _point_z(point):
        """Return a point Z value when present and finite."""
        if not hasattr(point, 'z'):
            return None
        z_value = point.z()
        return z_value if isfinite(z_value) else None

    @staticmethod
    def _node_elevations(links, line_elevations, tol):
        """Return checked node elevations from line endpoint Z values."""
        samples = defaultdict(list)
        for link, (start_z, end_z) in zip(links, line_elevations):
            start_node, end_node, _ = link
            if start_z is not None:
                samples[start_node].append(start_z)
            if end_z is not None:
                samples[end_node].append(end_z)

        elevations = {}
        for node_index, values in samples.items():
            if max(values) - min(values) > tol:
                return None
            elevations[node_index] = sum(values) / len(values)
        return elevations
