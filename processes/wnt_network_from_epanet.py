"""Import network layers from an EPANET input file."""

from pathlib import Path
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


NODE_EXTRA_FIELDS = (
    ("demand", QMetaType.Double),
    ("pattern", QMetaType.QString),
    ("head", QMetaType.Double),
    ("init_level", QMetaType.Double),
    ("min_level", QMetaType.Double),
    ("max_level", QMetaType.Double),
    ("diameter", QMetaType.Double),
    ("min_volume", QMetaType.Double),
    ("volume_curve", QMetaType.QString),
)


LINK_EXTRA_FIELDS = (
    ("minor_loss", QMetaType.Double),
    ("status", QMetaType.QString),
    ("setting", QMetaType.QString),
    ("pump_power", QMetaType.Double),
    ("pump_head", QMetaType.QString),
    ("pump_speed", QMetaType.Double),
    ("pump_pattern", QMetaType.QString),
    ("parameters", QMetaType.QString),
)


def set_output_layer_name(context, layer_id, name):
    """Set the display name for a generated Processing output layer."""
    if context is None or not layer_id:
        return
    try:
        details = context.layerToLoadOnCompletionDetails(layer_id)
        details.name = name
    except AttributeError:
        pass


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
<li>Node attributes include the EPANET input properties for junctions, reservoirs and tanks.</li>
<li>Link attributes include the EPANET input properties for pipes, pumps and valves.</li>
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
        output_name = Path(epanetf).stem

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
        for name, qtype in NODE_EXTRA_FIELDS:
            newfields.append(QgsField(name, qtype))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields,
            QgsWkbTypes.Point,
            crs
            )
        set_output_layer_name(context, node_id, f"{output_name}_nodes")

        # ADD NODES
        ncnt = 0
        ntot = len(nodes)
        for node in nodes:
            #add feature to sink
            ncnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(node.to_wkt()))
            f.setAttributes(
                [node.name(), node.get_type(), node.get_elevation()]
                + [node.epanet.get(name) for name, _ in NODE_EXTRA_FIELDS]
            )

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
        for name, qtype in LINK_EXTRA_FIELDS:
            newfields.append(QgsField(name, qtype))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs
            )
        set_output_layer_name(context, link_id, f"{output_name}_links")

        # ADD LINKS
        lcnt = 0
        ltot = len(links)
        for link in links:
            lcnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(link.to_wkt()))
            f.setAttributes(
                [
                    link.name(),
                    link.start(),
                    link.end(),
                    link.get_type(),
                    link.epanet.get('length'),
                    link.epanet.get('diameter'),
                    link.epanet.get('roughness'),
                ]
                + [link.epanet.get(name) for name, _ in LINK_EXTRA_FIELDS]
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

