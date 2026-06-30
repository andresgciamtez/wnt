"""Import network layers from an EPANET input file."""

import json
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
from ..utils.utils_parser import SectionedText, parse_tokens
from .messages import crs as log_crs
from .messages import error, finish, info, start


NODE_KEY_MAP = {
    "demand": "base_demand",
    "head": "total_head",
    "init_level": "initial_level",
    "min_level": "min_level",
    "max_level": "max_level",
    "diameter": "diameter",
    "min_volume": "min_volume",
    "volume_curve": "volume_curve",
}

LINK_KEY_MAP = {
    "minor_loss": "minor_loss",
    "setting": "valve_setting",
    "pump_power": "pump_power",
    "pump_head": "head_curve",
    "pump_speed": "pump_speed",
    "pump_pattern": "pump_pattern",
    "parameters": "pump_parameters",
}

NODE_JSON_KEYS = {
    "JUNCTION": (
        "base_demand",
        "demand_pattern",
        "demands",
        "emitter_coefficient",
        "initial_quality",
        "source_type",
        "source_quality",
        "source_pattern",
        "tag",
    ),
    "RESERVOIR": (
        "total_head",
        "head_pattern",
        "initial_quality",
        "source_type",
        "source_quality",
        "source_pattern",
        "tag",
    ),
    "TANK": (
        "initial_level",
        "min_level",
        "max_level",
        "diameter",
        "min_volume",
        "volume_curve",
        "initial_quality",
        "source_type",
        "source_quality",
        "source_pattern",
        "mixing_model",
        "mixing_fraction",
        "tank_reaction_coeff",
        "tag",
    ),
}

LINK_JSON_KEYS = {
    "PIPE": (
        "length",
        "diameter",
        "roughness",
        "minor_loss",
        "initial_status",
        "bulk_reaction_coeff",
        "wall_reaction_coeff",
        "tag",
    ),
    "CVPIPE": (
        "length",
        "diameter",
        "roughness",
        "minor_loss",
        "initial_status",
        "bulk_reaction_coeff",
        "wall_reaction_coeff",
        "tag",
    ),
    "PUMP": (
        "pump_parameters",
        "pump_power",
        "head_curve",
        "pump_speed",
        "pump_pattern",
        "initial_status",
        "energy_price",
        "energy_pattern",
        "efficiency_curve",
        "tag",
    ),
    "VALVE": (
        "diameter",
        "valve_type",
        "valve_setting",
        "minor_loss",
        "initial_status",
        "tag",
    ),
}


def section_tokens(sections, name):
    """Yield tokenized lines from one EPANET section."""
    for line in sections.get(name, []):
        tokens = parse_tokens(line)
        if tokens:
            yield tokens


def epanet_json(properties):
    """Serialize EPANET properties as stable compact JSON."""
    return json.dumps(properties, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def properties_template(keys):
    """Return an editable JSON template with all expected keys present."""
    return dict.fromkeys(keys)


def base_node_properties(node):
    """Return JSON-ready EPANET node properties from the core model."""
    node_type = node.get_type()
    properties = properties_template(NODE_JSON_KEYS.get(node_type, ()))
    for key, value in node.epanet.items():
        if key == "pattern":
            if node_type == "RESERVOIR":
                properties["head_pattern"] = value
            else:
                properties["demand_pattern"] = value
        else:
            properties[NODE_KEY_MAP.get(key, key)] = value
    return properties


def base_link_properties(link):
    """Return JSON-ready EPANET link properties from the core model."""
    link_type = link.get_type()
    keys = LINK_JSON_KEYS.get(link_type, LINK_JSON_KEYS["VALVE"])
    properties = properties_template(keys)
    for key, value in link.epanet.items():
        if key == "status":
            properties["initial_status"] = value
        else:
            properties[LINK_KEY_MAP.get(key, key)] = value
    if link_type not in {"PIPE", "CVPIPE", "PUMP"}:
        properties["valve_type"] = link_type
    return properties


def read_epanet_sections(path):
    """Read an EPANET INP file into section lines."""
    text = SectionedText()
    text.read(path)
    return text.sections


def extra_epanet_properties(sections):
    """Return supplemental node/link EPANET properties keyed by element id."""
    node_props = {}
    link_props = {}

    for tokens in section_tokens(sections, "DEMANDS"):
        if len(tokens) < 2:
            continue
        node_id = tokens[0]
        demand = {"base_demand": tokens[1]}
        if len(tokens) > 2:
            demand["demand_pattern"] = tokens[2]
        if len(tokens) > 3:
            demand["category"] = tokens[3]
        node_props.setdefault(node_id, {}).setdefault("demands", []).append(demand)

    for tokens in section_tokens(sections, "EMITTERS"):
        if len(tokens) >= 2:
            node_props.setdefault(tokens[0], {})["emitter_coefficient"] = tokens[1]

    for tokens in section_tokens(sections, "QUALITY"):
        if len(tokens) >= 2:
            node_props.setdefault(tokens[0], {})["initial_quality"] = tokens[1]

    for tokens in section_tokens(sections, "SOURCES"):
        if len(tokens) < 3:
            continue
        properties = node_props.setdefault(tokens[0], {})
        properties["source_type"] = tokens[1]
        properties["source_quality"] = tokens[2]
        if len(tokens) > 3:
            properties["source_pattern"] = tokens[3]

    for tokens in section_tokens(sections, "MIXING"):
        if len(tokens) < 2:
            continue
        properties = node_props.setdefault(tokens[0], {})
        properties["mixing_model"] = tokens[1]
        if len(tokens) > 2:
            properties["mixing_fraction"] = tokens[2]

    for tokens in section_tokens(sections, "REACTIONS"):
        if len(tokens) < 3:
            continue
        reaction_type = tokens[0].upper()
        if reaction_type == "TANK":
            node_props.setdefault(tokens[1], {})["tank_reaction_coeff"] = tokens[2]
        elif reaction_type == "BULK":
            link_props.setdefault(tokens[1], {})["bulk_reaction_coeff"] = tokens[2]
        elif reaction_type == "WALL":
            link_props.setdefault(tokens[1], {})["wall_reaction_coeff"] = tokens[2]

    for tokens in section_tokens(sections, "STATUS"):
        if len(tokens) >= 2:
            link_props.setdefault(tokens[0], {})["initial_status"] = " ".join(tokens[1:])

    for tokens in section_tokens(sections, "ENERGY"):
        if len(tokens) < 4 or tokens[0].upper() != "PUMP":
            continue
        key = tokens[2].lower()
        properties = link_props.setdefault(tokens[1], {})
        if key == "price":
            properties["energy_price"] = tokens[3]
        elif key == "pattern":
            properties["energy_pattern"] = tokens[3]
        elif key == "effic":
            properties["efficiency_curve"] = tokens[3]

    for tokens in section_tokens(sections, "TAGS"):
        if len(tokens) < 3:
            continue
        tag_type = tokens[0].upper()
        if tag_type == "NODE":
            node_props.setdefault(tokens[1], {})["tag"] = " ".join(tokens[2:])
        elif tag_type == "LINK":
            link_props.setdefault(tokens[1], {})["tag"] = " ".join(tokens[2:])

    return node_props, link_props


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
        return self.tr('Network from EPANET file')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Import')

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
<li>Node attributes are <code>id</code>, <code>type</code>, <code>elevation</code> and <code>epanet</code>.</li>
<li>Link attributes are <code>id</code>, <code>start</code>, <code>end</code>, <code>type</code> and <code>epanet</code>.</li>
<li>The <code>epanet</code> field stores type-specific EPANET properties as JSON.</li>
<li>Quality, source, mixing, reaction, status, energy, demand and tag data are preserved when present.</li>
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
        try:
            network.from_epanet(epanetf)
        except Exception as exc:
            error(feedback, str(exc))
            return {}
        nodes = network.nodes()
        links = network.links()
        sections = read_epanet_sections(epanetf)
        node_extra, link_extra = extra_epanet_properties(sections)

        # GENERATE NODES LAYER
        newfields = QgsFields()
        newfields.append(QgsField("id", QMetaType.QString))
        newfields.append(QgsField("type", QMetaType.QString))
        newfields.append(QgsField("elevation", QMetaType.Double))
        newfields.append(QgsField("epanet", QMetaType.QString))
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
            node_wkt = node.to_wkt()
            if node_wkt:
                f.setGeometry(QgsGeometry.fromWkt(node_wkt))
            properties = base_node_properties(node)
            properties.update(node_extra.get(node.name(), {}))
            f.setAttributes(
                [node.name(), node.get_type(), node.get_elevation(), epanet_json(properties)]
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
        newfields.append(QgsField("epanet", QMetaType.QString))
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
            link_wkt = link.to_wkt()
            if link_wkt:
                f.setGeometry(QgsGeometry.fromWkt(link_wkt))
            properties = base_link_properties(link)
            properties.update(link_extra.get(link.name(), {}))
            f.setAttributes(
                [
                    link.name(),
                    link.start(),
                    link.end(),
                    link.get_type(),
                    epanet_json(properties),
                ]
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
