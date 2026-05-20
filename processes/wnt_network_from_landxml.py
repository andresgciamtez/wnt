"""Import network layers from a LandXML pipe network."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsLineString,
                       QgsPoint,
                       QgsPointXY,
                       QgsProject,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsGeometry,
                       QgsVectorLayer,
                       QgsWkbTypes
                       )
from .base import WntProcessingAlgorithm
from ..utils import utils_landxml as landxml
from .messages import crs as log_crs
from .messages import finish, info, start


NODE_FIELD_TYPES = {
    "elevation": QMetaType.Double,
    "demand": QMetaType.Double,
    "init_lvl": QMetaType.Double,
    "min_lvl": QMetaType.Double,
    "max_lvl": QMetaType.Double,
    "invert_elv": QMetaType.Double,
    "rim_elv": QMetaType.Double,
    "max_depth": QMetaType.Double,
}


LINK_FIELD_TYPES = {
    "length": QMetaType.Double,
    "diameter": QMetaType.Double,
    "roughness": QMetaType.Double,
    "loss_coeff": QMetaType.Double,
    "geom_dim1": QMetaType.Double,
    "geom_dim2": QMetaType.Double,
    "inv_start": QMetaType.Double,
    "inv_end": QMetaType.Double,
    "slope": QMetaType.Double,
    "start_os": QMetaType.Double,
    "end_os": QMetaType.Double,
}


def qfield(name, field_types):
    """Build a field with the unified LandXML schema type."""
    return QgsField(name, field_types.get(name, QMetaType.QString))


def qfields(field_names, field_types):
    """Build a QgsFields collection from field names."""
    fields = QgsFields()
    for field in field_names:
        fields.append(qfield(field, field_types))
    return fields


def set_output_layer_name(context, layer_id, name):
    """Set the display name for a generated Processing output layer."""
    if context is None or not layer_id:
        return
    try:
        details = context.layerToLoadOnCompletionDetails(layer_id)
        details.name = name
    except AttributeError:
        pass


def layer_name(network, suffix):
    """Return the QGIS layer name for one imported LandXML network."""
    return f"{network['layer_base']}_{suffix}"


def node_feature(node, fields):
    """Build one node feature from a parsed LandXML node record."""
    feature = QgsFeature()
    point = QgsPointXY(node['x'], node['y'])
    feature.setGeometry(QgsGeometry.fromPointXY(point))
    feature.setAttributes([node.get(field) for field in fields])
    return feature


def link_feature(network, link, fields):
    """Build one link feature from a parsed LandXML link record."""
    feature = QgsFeature()
    start = network['nodes'][link['start']]
    end = network['nodes'][link['end']]
    spoint = QgsPoint(start['x'], start['y'])
    epoint = QgsPoint(end['x'], end['y'])
    feature.setGeometry(QgsGeometry(QgsLineString([spoint, epoint])))
    feature.setAttributes([link.get(field) for field in fields])
    return feature


def add_memory_layer(name, geometry, fields, crs, features):
    """Add an additional per-network memory layer to the current QGIS project."""
    uri = geometry
    if crs and crs.isValid():
        uri = f"{uri}?crs={crs.authid()}"
    layer = QgsVectorLayer(uri, name, "memory")
    provider = layer.dataProvider()
    provider.addAttributes(list(fields))
    layer.updateFields()
    provider.addFeatures(features)
    QgsProject.instance().addMapLayer(layer)
    return layer


class NetworkFromLandXMLAlgorithm(WntProcessingAlgorithm):
    """
    Build a network from a LandXML file.
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
<li>Creates unified <code>nodes</code> and <code>links</code> layers from all LandXML pipe network definitions.</li>
<li>Classifies networks as <code>water</code>, <code>sanitary</code> or <code>storm</code>.</li>
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
            epsg_code = imp_net['epsg_code']
            if not epsg_code.upper().startswith('EPSG:'):
                epsg_code = 'EPSG:' + epsg_code
            crs = QgsCoordinateReferenceSystem(epsg_code)
        elif 'wkt_crs' in imp_net:
            crs = QgsCoordinateReferenceSystem('WKT:' + imp_net['wkt_crs'])
        else:
            crs = QgsCoordinateReferenceSystem()

        # SHOW INFO
        start(feedback, self.displayName())
        log_crs(feedback, crs)

        first_network = next(iter(networks.values()), None)
        if first_network is None:
            return {}

        # GENERATE SINK LAYER
        node_fields = first_network["node_fields"]
        link_fields = first_network["link_fields"]
        newfields = qfields(node_fields, NODE_FIELD_TYPES)
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields,
            QgsWkbTypes.Point,
            crs
            )
        set_output_layer_name(context, node_id, layer_name(first_network, "nodes"))

        newfields = qfields(link_fields, LINK_FIELD_TYPES)
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs
            )
        set_output_layer_name(context, link_id, layer_name(first_network, "links"))

        netcnt = nodcnt = lnkcnt = 0
        # ADD NETWORK
        for index, network in enumerate(networks.values()):
            netcnt += 1
            node_fields = network["node_fields"]
            link_fields = network["link_fields"]
            node_features = [
                node_feature(node, node_fields)
                for node in network['nodes'].values()
            ]
            link_features = [
                link_feature(network, link, link_fields)
                for link in network['links'].values()
            ]
            nodcnt += len(node_features)
            lnkcnt += len(link_features)
            if index > 0:
                add_memory_layer(
                    layer_name(network, "nodes"),
                    "Point",
                    qfields(node_fields, NODE_FIELD_TYPES),
                    crs,
                    node_features,
                )
                add_memory_layer(
                    layer_name(network, "links"),
                    "LineString",
                    qfields(link_fields, LINK_FIELD_TYPES),
                    crs,
                    link_features,
                )
                continue
            # ADD NODES
            for f in node_features:
                node_sink.addFeature(f)

            # ADD LINKS
            for g in link_features:
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

