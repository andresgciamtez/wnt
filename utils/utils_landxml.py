"""LandXML pipe network parser."""

import re
import xml.etree.ElementTree as ET

NS = "{http://www.landxml.org/schema/LandXML-1.2}"

NODE_FIELDS = (
    "origin",
    "net_type",
    "id",
    "type",
    "elevation",
    "demand",
    "pattern",
    "init_lvl",
    "min_lvl",
    "max_lvl",
    "invert_elv",
    "rim_elv",
    "max_depth",
)

WATER_NODE_FIELDS = (
    "origin",
    "net_type",
    "id",
    "type",
    "elevation",
    "demand",
    "pattern",
    "init_lvl",
    "min_lvl",
    "max_lvl",
)

GRAVITY_NODE_FIELDS = (
    "origin",
    "net_type",
    "id",
    "type",
    "invert_elv",
    "rim_elv",
    "max_depth",
)

LINK_FIELDS = (
    "origin",
    "net_type",
    "id",
    "type",
    "start",
    "end",
    "length",
    "diameter",
    "roughness",
    "loss_coeff",
    "status",
    "material",
    "geom_shape",
    "geom_dim1",
    "geom_dim2",
    "inv_start",
    "inv_end",
)

WATER_LINK_FIELDS = (
    "origin",
    "net_type",
    "id",
    "type",
    "start",
    "end",
    "length",
    "diameter",
    "roughness",
    "loss_coeff",
    "status",
    "material",
)

GRAVITY_LINK_FIELDS = (
    "origin",
    "net_type",
    "id",
    "type",
    "start",
    "end",
    "length",
    "geom_shape",
    "geom_dim1",
    "geom_dim2",
    "roughness",
    "inv_start",
    "inv_end",
    "slope",
    "start_os",
    "end_os",
)

WATER = "water"
SANITARY = "sanitary"
STORM = "storm"
GRAVITY_TYPES = {SANITARY, STORM}


def xmlname(name):
    return NS + name


def _float(value, default=None):
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _round(value, digits=3):
    if value is None:
        return None
    return round(value, digits)


def _dim_m(value):
    """Return a LandXML section dimension in metres."""
    number = _float(value)
    if number is None:
        return None
    if abs(number) > 10:
        return round(number / 1000.0, 3)
    return round(number, 3)


def _diameter_mm(value):
    """Return a LandXML pressure pipe diameter in millimetres."""
    number = _float(value)
    if number is None:
        return None
    if abs(number) <= 10:
        return round(number * 1000.0, 3)
    return round(number, 3)


def _text(value):
    return value.strip().lower() if value else None


def _strip_text(value):
    return value.strip() if value else None


def _clean_id(value, origin=None):
    identifier = _strip_text(value)
    if not identifier:
        return None
    network = _strip_text(origin)
    if network:
        identifier = re.sub(
            r"\s*\(\s*" + re.escape(network) + r"\s*\)\s*$",
            "",
            identifier,
            flags=re.IGNORECASE,
        ).strip()
    return re.sub(r"\s+", "_", identifier)


def _layer_base_name(value):
    name = _strip_text(value) or "network"
    return re.sub(r"\s+", "_", name)


def fields_for_network_type(net_type):
    """Return node and link fields for one homologated network type."""
    if net_type == WATER:
        return WATER_NODE_FIELDS, WATER_LINK_FIELDS
    return GRAVITY_NODE_FIELDS, GRAVITY_LINK_FIELDS


def _network_type(pipenetwork):
    net_type = (
        pipenetwork.attrib.get("pipeNetworkType")
        or pipenetwork.attrib.get("pipeNetType")
        or ""
    ).strip().lower()
    if net_type in {WATER, SANITARY, STORM}:
        return net_type

    name = pipenetwork.attrib.get("name", "")
    if re.search(r"(agua|potable)", name, flags=re.IGNORECASE):
        return WATER
    if re.search(r"(san|res)", name, flags=re.IGNORECASE):
        return SANITARY
    if re.search(r"(plu|dren|llu)", name, flags=re.IGNORECASE):
        return STORM
    return STORM


def _new_record(fields):
    return {field: None for field in fields}


def _center_xy(struct):
    center = struct.find(xmlname("Center"))
    if center is None or not center.text:
        return None, None
    values = center.text.split()
    if len(values) < 2:
        return None, None
    return _float(values[0]), _float(values[1])


def _pressure_node_type(struct):
    source = " ".join(
        filter(None, (struct.attrib.get("name"), struct.attrib.get("desc"), struct.attrib.get("type")))
    )
    if re.search(r"tank|dep[oó]sito", source, flags=re.IGNORECASE):
        return "tank"
    if re.search(r"reservoir|embalse|fuente", source, flags=re.IGNORECASE):
        return "reservoir"
    return "junction"


def _gravity_node_type(struct):
    source = " ".join(
        filter(None, (struct.attrib.get("name"), struct.attrib.get("desc"), struct.attrib.get("type")))
    )
    if re.search(r"outfall|outlet|descarga|salida", source, flags=re.IGNORECASE):
        return "outfall"
    if re.search(r"storage|tank|dep[oó]sito", source, flags=re.IGNORECASE):
        return "storage"
    return "manhole"


def _inverts_by_pipe(struct, node_id, invert_elv, origin):
    inverts = {}
    for child in list(struct):
        if child.tag != xmlname("Invert"):
            continue
        pipe = _clean_id(child.attrib.get("refPipe"), origin)
        if not pipe:
            continue
        elev = _round(_float(child.attrib.get("elev"), invert_elv), 3)
        inverts[(pipe, node_id)] = elev
    return inverts


def _section_data(pipe):
    for child in list(pipe):
        if child.tag == xmlname("CircPipe"):
            dim = _dim_m(child.attrib.get("diameter"))
            return "circular", dim, 0.0
        if child.tag == xmlname("RectPipe"):
            height = _dim_m(child.attrib.get("height"))
            width = _dim_m(child.attrib.get("width"))
            return "box", height, width
        if child.tag == xmlname("EggPipe"):
            height = _dim_m(child.attrib.get("height") or child.attrib.get("diameter"))
            width = _dim_m(child.attrib.get("width"))
            return "egg", height, width
    return None, None, None


def _pipe_material(pipe):
    return _text(pipe.attrib.get("material") or pipe.attrib.get("mat"))


def _pipe_roughness(pipe, net_type):
    value = (
        pipe.attrib.get("roughness")
        or pipe.attrib.get("manning")
        or pipe.attrib.get("n")
    )
    if value is not None:
        return _float(value)
    return 140.0 if net_type == WATER else 0.013


def _water_link_type(pipe):
    source = " ".join(filter(None, (pipe.attrib.get("name"), pipe.attrib.get("desc"), pipe.attrib.get("type"))))
    if re.search(r"pump|bomba", source, flags=re.IGNORECASE):
        return "pump"
    if re.search(r"valve|v[aá]lvula", source, flags=re.IGNORECASE):
        return "valve"
    return "pipe"


def _gravity_link_type(pipe):
    source = " ".join(filter(None, (pipe.attrib.get("name"), pipe.attrib.get("desc"), pipe.attrib.get("type"))))
    if re.search(r"pump|bomba", source, flags=re.IGNORECASE):
        return "pump"
    if re.search(r"orifice|orificio", source, flags=re.IGNORECASE):
        return "orifice"
    if re.search(r"weir|vertedero", source, flags=re.IGNORECASE):
        return "weir"
    return "conduit"


def _node_record(origin, net_type, node_id, struct):
    node_fields, _ = fields_for_network_type(net_type)
    record = _new_record(node_fields)
    record["origin"] = origin
    record["net_type"] = net_type
    record["id"] = node_id

    sump = _round(_float(struct.attrib.get("elevSump") or struct.attrib.get("elevation")), 3)
    rim = _round(_float(struct.attrib.get("elevRim")), 3)
    if net_type == WATER:
        record["type"] = _pressure_node_type(struct)
        record["elevation"] = sump
        record["demand"] = 0.0
        record["pattern"] = struct.attrib.get("pattern")
        if record["type"] == "tank":
            record["init_lvl"] = _float(struct.attrib.get("initLevel"))
            record["min_lvl"] = _float(struct.attrib.get("minLevel"))
            record["max_lvl"] = _float(struct.attrib.get("maxLevel"))
    else:
        record["type"] = _gravity_node_type(struct)
        record["invert_elv"] = sump
        record["rim_elv"] = rim
        if sump is not None and rim is not None:
            record["max_depth"] = round(rim - sump, 3)
    return record


def _link_record(origin, net_type, link_id, pipe, inverts, nodes):
    _, link_fields = fields_for_network_type(net_type)
    record = _new_record(link_fields)
    start = _clean_id(pipe.attrib.get("refStart"), origin)
    end = _clean_id(pipe.attrib.get("refEnd"), origin)
    record["origin"] = origin
    record["net_type"] = net_type
    record["id"] = link_id
    record["start"] = start
    record["end"] = end
    record["length"] = _round(_float(pipe.attrib.get("length")), 3)

    shape, dim1, dim2 = _section_data(pipe)
    if net_type == WATER:
        record["type"] = _water_link_type(pipe)
        record["diameter"] = _diameter_mm(pipe.attrib.get("diameter") or dim1)
        record["roughness"] = _pipe_roughness(pipe, net_type)
        record["loss_coeff"] = _float(pipe.attrib.get("lossCoeff") or pipe.attrib.get("minorLoss"), 0.0)
        record["status"] = _text(pipe.attrib.get("status")) or "open"
        record["material"] = _pipe_material(pipe)
    else:
        record["type"] = _gravity_link_type(pipe)
        record["roughness"] = _pipe_roughness(pipe, net_type)
        record["geom_shape"] = shape
        record["geom_dim1"] = dim1
        record["geom_dim2"] = dim2 if dim2 is not None else 0.0
        record["inv_start"] = inverts.get((link_id, start))
        record["inv_end"] = inverts.get((link_id, end))
        start_invert = nodes[start]["invert_elv"]
        end_invert = nodes[end]["invert_elv"]
        if record["inv_start"] is not None and start_invert is not None:
            record["start_os"] = round(record["inv_start"] - start_invert, 3)
        if record["inv_end"] is not None and end_invert is not None:
            record["end_os"] = round(record["inv_end"] - end_invert, 3)
        length = record["length"]
        if length and record["inv_start"] is not None and record["inv_end"] is not None:
            record["slope"] = round((record["inv_start"] - record["inv_end"]) / length * 100, 4)
    return record


def network_from_xml(xmlfn):
    """Import all LandXML pipe networks into a unified WNT schema."""
    tree = ET.parse(xmlfn)
    root = tree.getroot()
    crs = root.find(xmlname("CoordinateSystem"))
    epsg_code = None
    wkt_crs = None
    if crs is not None:
        if "epsgCode" in crs.attrib:
            epsg_code = crs.attrib["epsgCode"]
        elif "ogcWktCode" in crs.attrib:
            wkt_crs = crs.attrib["ogcWktCode"]

    networks = {}
    for pipenetwork in root.iter(xmlname("PipeNetwork")):
        origin = _strip_text(pipenetwork.attrib.get("name")) or ""
        net_type = _network_type(pipenetwork)
        node_fields, link_fields = fields_for_network_type(net_type)
        nodes = {}
        links = {}
        inverts = {}

        for struct in pipenetwork.iter(xmlname("Struct")):
            if struct.attrib.get("desc") == "Dummy Null Structure for LandXML purposes":
                continue
            node_id = _clean_id(struct.attrib.get("name"), origin)
            if not node_id:
                continue
            node = _node_record(origin, net_type, node_id, struct)
            node["x"], node["y"] = _center_xy(struct)
            if net_type in GRAVITY_TYPES:
                inverts.update(_inverts_by_pipe(struct, node_id, node["invert_elv"], origin))
            nodes[node_id] = node

        for pipe in pipenetwork.iter(xmlname("Pipe")):
            link_id = _clean_id(pipe.attrib.get("name"), origin)
            start = _clean_id(pipe.attrib.get("refStart"), origin)
            end = _clean_id(pipe.attrib.get("refEnd"), origin)
            if not link_id or start not in nodes or end not in nodes:
                continue
            link = _link_record(origin, net_type, link_id, pipe, inverts, nodes)
            if net_type in GRAVITY_TYPES and (
                link["inv_start"] is None or link["inv_end"] is None
            ):
                continue
            links[link_id] = link

        networks[origin] = {
            "nodes": nodes,
            "links": links,
            "net_type": net_type,
            "node_fields": node_fields,
            "link_fields": link_fields,
            "layer_base": _layer_base_name(origin),
        }

    data = {"networks": networks, "node_fields": NODE_FIELDS, "link_fields": LINK_FIELDS}
    if epsg_code:
        data["epsg_code"] = epsg_code
    if wkt_crs:
        data["wkt_crs"] = wkt_crs
    return data
