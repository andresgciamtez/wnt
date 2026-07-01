"""Core network model and EPANET file helpers."""

import json
# XML parsing uses safe_xml_parse; ElementTree only builds XML output.
import xml.etree.ElementTree as ET  # nosec B405
from collections import defaultdict
from datetime import datetime, timezone
from math import dist, floor
from pathlib import Path
from .utils_parser import SectionedText, format_tokens, parse_tokens
from .safe_xml import parse as safe_xml_parse


XML_SCHEMA_VERSION = "1.0"
XML_DOMAIN_ORDER = ("epanet", "swmm", "landxml", "custom")


def pairwise(points):
    """Yield consecutive point pairs without requiring Python 3.10."""
    iterator = iter(points)
    try:
        previous = next(iterator)
    except StopIteration:
        return
    for current in iterator:
        yield previous, current
        previous = current


def xy(point):
    """Return the first two point coordinates as an ``(x, y)`` tuple."""
    try:
        return point[0], point[1]
    except (IndexError, TypeError):
        return point.x(), point.y()


def polyline_length(points):
    """Return the two-dimensional length of a polyline."""
    try:
        return sum(dist(xy(start), xy(end)) for start, end in pairwise(points))
    except (AttributeError, IndexError, TypeError, ValueError) as exc:
        raise ValueError("Bad geometry, it must be a sequence of (x, y) points.") from exc


def _normalise_domain(domain):
    value = str(domain or "custom").strip().lower()
    return value or "custom"


def _ensure_properties(element):
    properties = getattr(element, "properties", None)
    if properties is None:
        properties = {}
        element.properties = properties
    properties["epanet"] = element.epanet
    return properties


def _ordered_domains(properties):
    domains = [domain for domain in XML_DOMAIN_ORDER if domain in properties]
    domains.extend(sorted(domain for domain in properties if domain not in domains))
    return domains


def _serialise_property_value(value):
    if value is None:
        return "null", ""
    if isinstance(value, bool):
        return "bool", "true" if value else "false"
    if isinstance(value, int) and not isinstance(value, bool):
        return "int", str(value)
    if isinstance(value, float):
        return "float", repr(value)
    if isinstance(value, (list, dict)):
        return "json", json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "string", str(value)


def _parse_property_value(kind, value):
    if kind == "null":
        return None
    if kind == "bool":
        return str(value).lower() in ("1", "true", "yes")
    if kind == "int":
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    if kind == "float":
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    if kind == "json":
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return value
    return value


def _write_metadata(parent, metadata):
    if not metadata:
        return
    metadata_element = ET.SubElement(parent, "metadata")
    for name in sorted(metadata):
        kind, value = _serialise_property_value(metadata[name])
        ET.SubElement(metadata_element, "property", {"name": str(name), "type": kind, "value": value})


def _read_metadata(parent):
    metadata = {}
    metadata_element = parent.find("metadata")
    if metadata_element is None:
        return metadata
    for property_element in metadata_element.findall("property"):
        name = property_element.get("name")
        if name:
            metadata[name] = _parse_property_value(
                property_element.get("type", "string"), property_element.get("value", "")
            )
    return metadata


def _write_properties(parent, element):
    properties = _ensure_properties(element)
    for domain in _ordered_domains(properties):
        values = properties.get(domain) or {}
        if not values:
            continue
        properties_element = ET.SubElement(parent, "properties", {"domain": domain})
        for name in sorted(values):
            kind, value = _serialise_property_value(values[name])
            ET.SubElement(properties_element, "property", {"name": str(name), "type": kind, "value": value})


def _read_properties(parent, element):
    for properties_element in parent.findall("properties"):
        domain = _normalise_domain(properties_element.get("domain"))
        values = {}
        for property_element in properties_element.findall("property"):
            name = property_element.get("name")
            if name:
                values[name] = _parse_property_value(
                    property_element.get("type", "string"), property_element.get("value", "")
                )
        element.set_properties(domain, values)


def _link_property_length(link):
    length = link.get_length()
    if length is not None:
        return length
    properties = _ensure_properties(link)
    for domain in _ordered_domains(properties):
        value = properties.get(domain, {}).get("length")
        if value not in (None, ""):
            return value
    geometry = link.get_geometry()
    if geometry:
        return polyline_length(geometry)

def format_id(number, mask):
    '''Format n: int. Mask: "prefix$$$suffix". $ = 1 decimal positions.'''
    if '$' not in mask:
        return mask + str(number)
    digits = ''
    while digits + '$' in mask:
        digits += '$'
    prefix, _, suffix = mask.partition(digits)
    return prefix + str(number).zfill(len(digits)) + suffix

def net_from_linestrings(linestrings, tol):
    """Build a network from linestrings.

    Return: (nodes, links) tuple. Where:
    nodes: [(x, y), ..]. id: x, y: float.
    links: [(start, end, linestring), ..]. start and end: int, connexion nodes.
    linestring: [(start-node) .. (end-node), ..]. Adjusted geometry.

    Parameters
    ----------
    linestring: list, [(x, y), ..]. x, y: float
    tol: float, fusion distance, default 0.0
    """
    ERR_MSG1 = 'Zero length LineString.'
    ERR_MSG2 = 'Looped LineString.'

    endpoints = []
    for index, line in enumerate(linestrings):
        if polyline_length(line) == 0:
            raise Exception(ERR_MSG1)

        start = xy(line[0])
        end = xy(line[-1])
        if dist(start, end) < tol:
            raise Exception(ERR_MSG2)

        endpoints.append((-(index + 1), start))
        endpoints.append((index + 1, end))

    parents = list(range(len(endpoints)))
    ranks = [0] * len(endpoints)

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def union(left, right):
        left_root = find(left)
        right_root = find(right)
        if left_root == right_root:
            return
        if ranks[left_root] < ranks[right_root]:
            parents[left_root] = right_root
        elif ranks[left_root] > ranks[right_root]:
            parents[right_root] = left_root
        else:
            parents[right_root] = left_root
            ranks[left_root] += 1

    if tol > 0:
        grid = defaultdict(list)
        for endpoint_index, (_, point) in enumerate(endpoints):
            x, y = point
            cell = floor(x / tol), floor(y / tol)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for candidate in grid[(cell[0] + dx, cell[1] + dy)]:
                        if dist(point, endpoints[candidate][1]) <= tol:
                            union(endpoint_index, candidate)
            grid[cell].append(endpoint_index)
    else:
        seen = {}
        for endpoint_index, (_, point) in enumerate(endpoints):
            if point in seen:
                union(endpoint_index, seen[point])
            else:
                seen[point] = endpoint_index

    endpoint_nodes = {}
    cluster_nodes = {}
    sums = []
    counts = []
    for endpoint_index, (endpoint_id, point) in enumerate(endpoints):
        root = find(endpoint_index)
        if root not in cluster_nodes:
            cluster_nodes[root] = len(sums)
            sums.append([0.0, 0.0])
            counts.append(0)
        node_index = cluster_nodes[root]
        endpoint_nodes[endpoint_id] = node_index
        sums[node_index][0] += point[0]
        sums[node_index][1] += point[1]
        counts[node_index] += 1

    nodes = [
        (point_sum[0] / count, point_sum[1] / count)
        for point_sum, count in zip(sums, counts)
    ]

    links = []
    for index, line in enumerate(linestrings):
        start = endpoint_nodes[-(index + 1)]
        end = endpoint_nodes[index + 1]
        geometry = [xy(point) for point in line]
        geometry[0] = nodes[start]
        geometry[-1] = nodes[end]
        links.append([start, end, geometry])

    return (nodes, links)


class WntNode:
    """WntNode class."""

    MAX_NAME_LEN = 15
    NODE_TYPES = ['JUNCTION', 'RESERVOIR', 'TANK', 'OUTFALL', 'DIVIDER',
                  'STORAGE', 'MANHOLE', 'OUTLET']

    def __init__(self, name):
        # ERR_MSG = 'Name too long. MAX LEN = {}.'.format(WntNode.MAX_NAME_LEN)
        # if len(name) > WntNode.MAX_NAME_LEN:
        #     raise Exception(ERR_MSG)
        self._name = name
        self._x = None
        self._y = None
        self._elevation = None
        self._type = None
        self.epanet = {}
        self.properties = {"epanet": self.epanet}

    def name(self):
        """Return name (epanet ID)."""
        return self._name

    def get_properties(self, domain):
        """Return editable properties for one external schema domain."""
        domain = _normalise_domain(domain)
        if domain == "epanet":
            return self.epanet
        return _ensure_properties(self).setdefault(domain, {})

    def set_properties(self, domain, properties):
        """Replace properties for one external schema domain."""
        domain = _normalise_domain(domain)
        values = dict(properties or {})
        if domain == "epanet":
            self.epanet.clear()
            self.epanet.update(values)
            _ensure_properties(self)["epanet"] = self.epanet
        else:
            _ensure_properties(self)[domain] = values

    def all_properties(self):
        """Return all non-empty external schema property domains."""
        return {domain: dict(values) for domain, values in _ensure_properties(self).items() if values}

    def set_geometry(self, coor):
        """Set node geometry where coor is a float tuple (x, y)."""
        ERR_MSG = 'Bad geometry, it must be a (x, y) float tuple.'
        try:
            self._x = float(coor[0])
            self._y = float(coor[1])
        except (IndexError, TypeError, ValueError):
            raise Exception(ERR_MSG)

    def get_geometry(self):
        """Get node geometry as a float tuple (x, y)."""
        return (self._x, self._y)

    def set_elevation(self, z):
        """Set node elevation."""
        ERR_MSG = 'Bad elevation.'
        try:
            self._elevation = float(z)
        except (TypeError, ValueError):
            raise Exception(ERR_MSG)

    def get_elevation(self):
        """Get node elevation."""
        return self._elevation

    def set_type(self, nodetype):
        """Set node type."""
        ERR_MSG = 'Incorrect type, it must be: {}.'.format(WntNode.NODE_TYPES)
        try:
            self._type = nodetype.upper()
        except AttributeError:
            raise Exception(ERR_MSG)
        if self._type not in WntNode.NODE_TYPES:
            self._type = None
            raise Exception(ERR_MSG)

    def get_type(self):
        """Get node type if it is defined, otherwise None."""
        return self._type

    def from_wkt(self, wkt):
        """Set geometry from a WKT format point, 'Point(x y).'"""
        ERR_MSG = "Incorrect WKT point format, it must be 'Point[z](x y [z]).'"
        try:
            point = wkt.upper()
            for clean in ['POINT', 'Z', '(', ')', '"', '\n']:
                point = point.replace(clean, '')
            point = point.strip().split()
            point = float(point[0]), float(point[1])
            self.set_geometry(point)
        except (AttributeError, IndexError, TypeError, ValueError):
            raise Exception(ERR_MSG)

    def to_wkt(self):
        """Return the node geometry in WKT format, 'Point (x y).'"""
        if self._x is not None and self._y is not None:
            return 'Point({} {})'.format(self._x, self._y)


class WntLink:
    """WntLink class."""

    MAX_NAME_LEN = 15
    LINK_TYPES = ['PIPE', 'CVPIPE', 'PUMP', 'PRV', 'PSV', 'PBV', 'FCV',
                  'TCV', 'GPV', 'VALVE', 'CONDUIT', 'ORIFICE', 'WEIR', 'OUTLET']

    def __init__(self, name, start, end):
        # ERR_MSG = 'Name too long. MAX LEN = {}.'.format(WntNode.MAX_NAME_LEN)
        # if max([len(str(n)) for n in [name, start, end]]) > WntNode.MAX_NAME_LEN:
        #     raise Exception(ERR_MSG)
        self._name = name
        self._start = start
        self._end = end
        self._linestring = None
        self._length = None
        self._type = None
        self.epanet = {}
        self.properties = {"epanet": self.epanet}

    def name(self):
        """Return name (epanet ID)."""
        return self._name

    def start(self):
        """Return the link start (node name)."""
        return self._start

    def end(self):
        """Return the link end (node name)."""
        return self._end

    def get_properties(self, domain):
        """Return editable properties for one external schema domain."""
        domain = _normalise_domain(domain)
        if domain == "epanet":
            return self.epanet
        return _ensure_properties(self).setdefault(domain, {})

    def set_properties(self, domain, properties):
        """Replace properties for one external schema domain."""
        domain = _normalise_domain(domain)
        values = dict(properties or {})
        if domain == "epanet":
            self.epanet.clear()
            self.epanet.update(values)
            _ensure_properties(self)["epanet"] = self.epanet
        else:
            _ensure_properties(self)[domain] = values

    def all_properties(self):
        """Return all non-empty external schema property domains."""
        return {domain: dict(values) for domain, values in _ensure_properties(self).items() if values}

    def set_length(self, length):
        """Set the common link length metadata."""
        self._length = float(length)

    def get_length(self):
        """Return the common link length metadata when available."""
        return self._length

    def set_geometry(self, linestring):
        """Set link geometry as a list of coordinate tuples [(x, y) ...]."""
        ERR_MSG1 = 'Bad geometry, at least 2 points are required.'
        ERR_MSG2 = 'Looped linestring.'
        ERR_MSG3 = 'Bad geometry, it must be a list [(x, y) ...].'
        ERR_MSG4 = 'Linestring has zero length.'
        if len(linestring) < 2:
            raise Exception(ERR_MSG1)
        if linestring[0] == linestring[-1]:
            raise Exception(ERR_MSG2)
        try:
            self._linestring = [(float(x), float(y)) for x, y in linestring]
        except (TypeError, ValueError):
            raise Exception(ERR_MSG3)
        if polyline_length(self._linestring) == 0:
            self._linestring = None
            raise Exception(ERR_MSG4)

    def get_geometry(self):
        """Return link geometry as a list of coordinate tuples [(x, y) ...]."""
        return self._linestring

    def get_vertices(self):
        """Return the middle vertices."""
        if self._linestring:
            return self._linestring[1:-1]
        return []

    def set_type(self, linktype):
        """Set link type."""
        ERR_MSG = 'Bad type, it must be: {}'.format(WntLink.LINK_TYPES)
        try:
            linktype = linktype.upper()
            self._type = linktype
        except AttributeError:
            raise Exception(ERR_MSG)
        if self._type not in WntLink.LINK_TYPES:
            self._type = None
            raise Exception(ERR_MSG)

    def get_type(self):
        """Get link type if it is defined, otherwise None."""
        return self._type

    def from_wkt(self, wkt):
        """Set the geometry from a WKT format line, 'LineString(x y, ...)'."""
        ERR_MSG1 = "Incorrect WKT format, it must be 'LineString[z](x y[z], ...)'."
        ERR_MSG2 = " Multi-geometry is not supported."
        try:
            txt = wkt.upper()
        except AttributeError:
            raise Exception(ERR_MSG1)
        if 'MULTI' in txt:
            raise Exception(ERR_MSG2)
        try:
            for clean in ['LINESTRING', 'Z', '(', ')', '"', '\n']:
                txt = txt.replace(clean, '')
            points = []
            for point in txt.strip().split(','):
                point = point.strip().split(' ')
                points.append((float(point[0]), float(point[1])))
        except (IndexError, TypeError, ValueError):
            raise Exception(ERR_MSG1)
        self.set_geometry(points)

    def to_wkt(self):
        """Return the link geometry in WKT format. 'LineString(x y, ...)'."""
        if self._linestring:
            txt = 'LineString('
            for point in self._linestring[0:-1]:
                txt += str(point[0]) + ' ' + str(point[1]) + ','
            point = self._linestring[-1]
            txt += str(point[0]) + ' ' + str(point[1]) + ')'
            return txt

class WntNetwork:
    """WntNetwork class."""
    def __init__(self):
        self._nodes = []
        self._links = []
        self._node_map = {} # name -> index
        self._link_map = {} # name -> index

    def nodes(self):
        """Return the network nodes"""
        return self._nodes

    def links(self):
        """Return the network links"""
        return self._links

    def clear(self):
        """Remove all nodes and links from the network."""
        self._nodes, self._links, self._node_map, self._link_map = [], [], {}, {}

    def add_node(self, node):
        """Add a node to the network."""
        ERR_MSG = 'Bad type. Must be Node.'
        if not isinstance(node, WntNode):
            raise Exception(ERR_MSG)
        if node.name() not in self._node_map:
            self._node_map[node.name()] = len(self._nodes)
        self._nodes.append(node)

    def add_link(self, link):
        """Add a link to the network."""
        ERR_MSG = 'Bad type. Must be Node.'
        if not isinstance(link, WntLink):
            raise Exception(ERR_MSG)
        if link.name() not in self._link_map:
            self._link_map[link.name()] = len(self._links)
        self._links.append(link)

    def get_nodeindex(self, nodeid):
        """Return the index of the labeled node: nodeid, None  if not exists."""
        return self._node_map.get(nodeid)

    def get_linkindex(self, linkid):
        """Return the index of the labeled link: linkid, None if not exists."""
        return self._link_map.get(linkid)


    @staticmethod
    def _read_or_create_xml(xml_file):
        xml_path = Path(xml_file)
        if xml_path.exists() and xml_path.stat().st_size > 0:
            tree = safe_xml_parse(str(xml_path))
            root = tree.getroot()
            if root.tag != "wntNetworkStore":
                raise Exception("Invalid WNT XML file: expected wntNetworkStore root.")
            root.set("schemaVersion", root.get("schemaVersion", XML_SCHEMA_VERSION))
            return tree, root
        root = ET.Element("wntNetworkStore", {"schemaVersion": XML_SCHEMA_VERSION})
        return ET.ElementTree(root), root

    @staticmethod
    def _find_network_element(root, network_id=None):
        networks = root.findall("network")
        if network_id is None:
            if not networks:
                raise Exception("WNT XML file does not contain networks.")
            return networks[0]
        network_id = str(network_id)
        for network in networks:
            if network.get("id") == network_id:
                return network
        raise Exception("Network not found in WNT XML file: {}".format(network_id))

    @staticmethod
    def _get_or_create_network_element(root, network_id, crs=None, metadata=None):
        network_id = str(network_id or "network")
        for network in root.findall("network"):
            if network.get("id") == network_id:
                break
        else:
            network = ET.SubElement(root, "network", {"id": network_id})
        network.set("id", network_id)
        network.set("name", str((metadata or {}).get("name") or network.get("name") or network_id))
        if crs:
            network.set("crs", str(crs))
        return network

    @staticmethod
    def _select_version_element(network, version_id=None):
        versions = network.findall("version")
        if not versions:
            raise Exception("Network does not contain versions.")
        if version_id in (None, ""):
            return versions[-1]
        version_id = str(version_id)
        for version in versions:
            if version.get("id") == version_id:
                return version
        raise Exception("Network version not found in WNT XML file: {}".format(version_id))

    def to_xml(
        self,
        xml_file,
        version_id,
        network_id="network",
        model_type="generic",
        crs=None,
        metadata=None,
        replace=True,
    ):
        """Store the network in a multiversion WNT XML file."""
        if not version_id:
            raise Exception("Version id is required.")
        metadata = dict(metadata or {})
        tree, root = self._read_or_create_xml(xml_file)
        network = self._get_or_create_network_element(root, network_id, crs, metadata)

        for version in list(network.findall("version")):
            if version.get("id") != str(version_id):
                continue
            if not replace:
                raise Exception("Network version already exists: {}".format(version_id))
            network.remove(version)

        version = ET.Element(
            "version",
            {
                "id": str(version_id),
                "created": str(metadata.get("created") or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")),
                "modelType": str(model_type or "generic").lower(),
                "source": str(metadata.get("source") or "wnt"),
            },
        )
        _write_metadata(version, metadata)

        node_ids = {}
        nodes_element = ET.SubElement(version, "nodes")
        for node in sorted(self.nodes(), key=lambda item: item.name()):
            if node.name() in node_ids:
                raise Exception("Duplicated node id in network: {}".format(node.name()))
            node_ids[node.name()] = node
            node_type = node.get_type()
            if not node_type:
                raise Exception("Node has no type: {}".format(node.name()))
            x, y = node.get_geometry()
            if x is None or y is None:
                raise Exception("Node has no geometry: {}".format(node.name()))
            attributes = {"id": str(node.name()), "type": str(node_type), "x": str(x), "y": str(y)}
            if node.get_elevation() is not None:
                attributes["elevation"] = str(node.get_elevation())
            node_element = ET.SubElement(nodes_element, "node", attributes)
            _write_properties(node_element, node)

        link_ids = set()
        links_element = ET.SubElement(version, "links")
        for link in sorted(self.links(), key=lambda item: item.name()):
            if link.name() in link_ids:
                raise Exception("Duplicated link id in network: {}".format(link.name()))
            link_ids.add(link.name())
            if link.start() not in node_ids or link.end() not in node_ids:
                raise Exception("Link references undefined nodes: {}".format(link.name()))
            link_type = link.get_type()
            if not link_type:
                raise Exception("Link has no type: {}".format(link.name()))
            geometry = link.get_geometry()
            if not geometry:
                geometry = [node_ids[link.start()].get_geometry(), node_ids[link.end()].get_geometry()]
            attributes = {"id": str(link.name()), "start": str(link.start()), "end": str(link.end()), "type": str(link_type)}
            length = _link_property_length(link)
            if length is not None:
                attributes["length"] = str(length)
            link_element = ET.SubElement(links_element, "link", attributes)
            vertices_element = ET.SubElement(link_element, "vertices")
            for x, y in geometry:
                ET.SubElement(vertices_element, "vertex", {"x": str(x), "y": str(y)})
            _write_properties(link_element, link)

        network.append(version)
        if hasattr(ET, "indent"):
            ET.indent(tree, space="  ")
        tree.write(str(xml_file), encoding="utf-8", xml_declaration=True)

    def from_xml(self, xml_file, version_id=None, network_id=None):
        """Load one network version from a WNT XML file."""
        tree = safe_xml_parse(str(xml_file))
        root = tree.getroot()
        if root.tag != "wntNetworkStore":
            raise Exception("Invalid WNT XML file: expected wntNetworkStore root.")
        network = self._find_network_element(root, network_id)
        version = self._select_version_element(network, version_id)

        self.clear()
        self.xml_network_id = network.get("id")
        self.xml_version_id = version.get("id")
        self.xml_model_type = version.get("modelType")
        self.xml_crs = network.get("crs")
        self.xml_metadata = _read_metadata(version)

        nodes_element = version.find("nodes")
        if nodes_element is None:
            raise Exception("Network version does not contain nodes.")
        for node_element in nodes_element.findall("node"):
            node_id = node_element.get("id")
            if not node_id:
                raise Exception("Node without id in WNT XML file.")
            node = WntNode(node_id)
            if node_element.get("type"):
                node.set_type(node_element.get("type"))
            node.set_geometry((node_element.get("x"), node_element.get("y")))
            if node_element.get("elevation") not in (None, ""):
                node.set_elevation(node_element.get("elevation"))
            _read_properties(node_element, node)
            self.add_node(node)

        links_element = version.find("links")
        if links_element is None:
            raise Exception("Network version does not contain links.")
        for link_element in links_element.findall("link"):
            link_id = link_element.get("id")
            start = link_element.get("start")
            end = link_element.get("end")
            if not link_id or not start or not end:
                raise Exception("Link without id, start or end in WNT XML file.")
            if self.get_nodeindex(start) is None or self.get_nodeindex(end) is None:
                raise Exception("Link references undefined nodes: {}".format(link_id))
            link = WntLink(link_id, start, end)
            if link_element.get("type"):
                link.set_type(link_element.get("type"))
            if link_element.get("length") not in (None, ""):
                link.set_length(link_element.get("length"))
            vertices_element = link_element.find("vertices")
            geometry = []
            if vertices_element is not None:
                for vertex_element in vertices_element.findall("vertex"):
                    geometry.append((float(vertex_element.get("x")), float(vertex_element.get("y"))))
            if not geometry:
                geometry = [
                    self.nodes()[self.get_nodeindex(start)].get_geometry(),
                    self.nodes()[self.get_nodeindex(end)].get_geometry(),
                ]
            link.set_geometry(geometry)
            _read_properties(link_element, link)
            self.add_link(link)
        return self


    def from_epanet(self, epanetf):
        """Make a network from a epanet file, reading:

        Node data: id, type, elevation and coordinates.
        Link data: id, type, start, end, type, vertices.

        IT IS PENDING TO IMPLEMENT THE REST OF PARAMETERS !

        Parameters
        ----------
        epanetf: epanet file name (*.inp), input epanet model
        """

        # READ EPANET FILE
        self._nodes = []
        self._links = []
        self._node_map = {}
        self._link_map = {}
        htext = SectionedText()
        htext.read(epanetf)
        sections = htext.sections

        # INPUT JUNCTIONS # ID Elev Demand Pattern
        for line in  sections.get('JUNCTIONS', []):
            tmp = parse_tokens(line)
            junction = WntNode(tmp[0])
            junction.set_type('JUNCTION')
            junction.set_elevation(tmp[1])
            junction.epanet['demand'] = tmp[2] if len(tmp) > 2 else None
            junction.epanet['pattern'] = tmp[3] if len(tmp) > 3 else None
            self.add_node(junction)

        # INPUT RESERVOIRS # ID Head Pattern
        for line in sections.get('RESERVOIRS', []):
            tmp = parse_tokens(line)
            reservoir = WntNode(tmp[0])
            reservoir.set_type('RESERVOIR')
            reservoir.set_elevation(tmp[1])
            reservoir.epanet['head'] = tmp[1]
            reservoir.epanet['pattern'] = tmp[2] if len(tmp) > 2 else None
            self.add_node(reservoir)

        # INPUT TANKS # ID Elevation InitLevel MinLevel MaxLevel
        # Diameter MinVol VolCurve
        for line in  sections.get('TANKS', []):
            tmp = parse_tokens(line)
            tank = WntNode(tmp[0])
            tank.set_type('TANK')
            tank.set_elevation(tmp[1])
            tank.epanet['init_level'] = tmp[2] if len(tmp) > 2 else None
            tank.epanet['min_level'] = tmp[3] if len(tmp) > 3 else None
            tank.epanet['max_level'] = tmp[4] if len(tmp) > 4 else None
            tank.epanet['diameter'] = tmp[5] if len(tmp) > 5 else None
            tank.epanet['min_volume'] = tmp[6] if len(tmp) > 6 else None
            tank.epanet['volume_curve'] = tmp[7] if len(tmp) > 7 else None
            self.add_node(tank)

        # COORDINATES
        for line in sections.get('COORDINATES', []):
            nid, x, y = parse_tokens(line)
            index = self.get_nodeindex(nid)
            if index is None:
                continue
            self._nodes[index].set_geometry((float(x), float(y)))

        # INPUT PIPES # ID Node1 Node2 Length Diameter Roughness MinorLoss
        # Status
        for line in  sections.get('PIPES', []):
            tmp = parse_tokens(line)
            lid, n1, n2 = tmp[0:3]
            s = tmp[-1]
            pipe = WntLink(lid, n1, n2)
            if s == "CV":
                pipe.set_type('CVPIPE')
            else:
                pipe.set_type('PIPE')
            pipe.epanet['length'] = tmp[3]
            pipe.epanet['diameter'] = tmp[4]
            pipe.epanet['roughness'] = tmp[5]
            pipe.epanet['minor_loss'] = tmp[6] if len(tmp) > 6 else None
            pipe.epanet['status'] = tmp[7] if len(tmp) > 7 else None
            self.add_link(pipe)

        # INPUT PUMPS #  # ID Node1 Node2 Parameters
        for line in  sections.get('PUMPS', []):
            tmp = parse_tokens(line)
            lid, n1, n2 = tmp[0:3]
            pump = WntLink(lid, n1, n2)
            pump.set_type('PUMP')
            pump.epanet['parameters'] = ' '.join(tmp[3:])
            for key, value in zip(tmp[3::2], tmp[4::2]):
                key = key.lower()
                if key == 'power':
                    pump.epanet['pump_power'] = value
                elif key == 'head':
                    pump.epanet['pump_head'] = value
                elif key == 'speed':
                    pump.epanet['pump_speed'] = value
                elif key == 'pattern':
                    pump.epanet['pump_pattern'] = value
            self.add_link(pump)

        # INPUT VALVES # ID Node1 Node2 Diameter Type Setting MinorLoss
        for line in  sections.get('VALVES', []):
            tmp = parse_tokens(line)
            lid, n1, n2 = tmp[0:3]
            t = tmp[4]
            valve = WntLink(lid, n1, n2)
            valve.set_type(t)
            valve.epanet['diameter'] = tmp[3]
            valve.epanet['setting'] = tmp[5] if len(tmp) > 5 else None
            valve.epanet['minor_loss'] = tmp[6] if len(tmp) > 6 else None
            self.add_link(valve)

        # VERTICES
        for link in self.links():
            start_index = self.get_nodeindex(link.start())
            end_index = self.get_nodeindex(link.end())
            if start_index is None or end_index is None:
                continue
            start_geometry = self._nodes[start_index].get_geometry()
            end_geometry = self._nodes[end_index].get_geometry()
            if None in start_geometry or None in end_geometry:
                continue
            link.set_geometry([start_geometry, end_geometry])

        for line in sections.get('VERTICES', []):
            nid, x, y = parse_tokens(line)
            index = self.get_linkindex(nid)
            if index is None:
                continue
            poly = self._links[index].get_geometry()
            if poly:
                poly.insert(-1, (float(x), float(y)))

    def to_epanet(self, inpf, tplf):
        """Export a network (nodes and links) to an epanet file.

        Data exported:
            [JUNTIONS]
            'id' and 'elevation'
            [RESERVOIRS]
            'id' and 'elevation'
            [TANKS]
            'id' and 'elevation'
            [PIPES]
            'id', 'start', 'end' and 'length'
            [PUMPS]
            'id', 'start' and 'end'
            [VALVES]
            'id', 'start', and 'end'
            [COORDINATES]
            'id', 'x' and 'y'
            [VERTICES]
            'id', 'x' and 'y'

        Parameters
        ----------
        inpf: str, output epanet file name (*.inp)
        tplf: str, input template epanet file name (*.inp)
        """

        # READ EPANET FILE TEMPLATE
        htext = SectionedText()

        # LOAD TEMPLATE
        htext.read(tplf)
        sections = htext.sections

        # ADD NODES/COORDINATES TO SECTION
        for node in self.nodes():
            nodetype = node.get_type()
            if nodetype not in ['JUNCTION', 'RESERVOIR', 'TANK']:
                continue

            if nodetype == 'JUNCTION':
                if node.get_elevation():
                    tmp = (node.name(), node.get_elevation(), 0.0)
                else:
                    tmp = (node.name(), 0.0, 0.0)
                sections['JUNCTIONS'].append(format_tokens(tmp))

            if nodetype == 'RESERVOIR':
                if node.get_elevation():
                    tmp = (node.name(), node.get_elevation())
                else:
                    tmp = (node.name(), 0.0)
                sections['RESERVOIRS'].append(format_tokens(tmp))

            if nodetype == 'TANK':
                if node.get_elevation():
                    tmp = (node.name(), node.get_elevation(), 0.0, 0.0, 0.0, 0.0, 0.0)
                else:
                    tmp = (node.name(), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
                sections['TANKS'].append(format_tokens(tmp))

            x, y = node.get_geometry()
            line = format_tokens((node.name(), x, y))
            sections['COORDINATES'].append(line)

        # ADD LINKS/VERTICES TO SECTION
        for link in self.links():
            linktype = link.get_type()
            if linktype not in ['PIPE', 'CVPIPE', 'PUMP', 'PRV', 'PSV', 'PBV', 'FCV', 'TCV', 'GPV', None]:
                continue
            # (id,start,end, ...
            tmp = (link.name(), link.start(), link.end())
            if linktype in ['PIPE', 'CVPIPE'] or not linktype:
                # length,diameter,roughness,minorLoss, ...
                length = link.get_length()
                if length is None and 'length' in link.epanet:
                    length = link.epanet['length']
                if length is not None:
                    tmp = tmp + (length, 0.0, 0.0, 0.0)
                else:
                    tmp = tmp + (0.0, 0.0, 0.0, 0.0)

                # status)
                if linktype == 'CVPIPE':
                    tmp = tmp + ('CV',)
                else:
                    tmp = tmp + ('Open',)
                sections['PIPES'].append(format_tokens(tmp))

            elif linktype == 'PUMP':
                tmp = (link.name(), link.start(), link.end())
                sections['PUMPS'].append(format_tokens(tmp))

            elif linktype in ['PRV', 'PSV', 'PBV', 'FCV', 'TCV', 'GPV']:
                tmp = (link.name(), link.start(), link.end(), 0.0, linktype)
                tmp = tmp + (0.0, 0.0)
                sections['VALVES'].append(format_tokens(tmp))

            vertices = link.get_vertices()
            if vertices:
                for vertice in vertices:
                    tmp = (link.name(), vertice[0], vertice[1])
                    sections['VERTICES'].append(format_tokens(tmp))

        # RESIZE [BACKDROP]
        x1, y1, x2, y2 = 1e12, 1e12, -1e12, -1e12
        for node in self.nodes():
            x, y = node.get_geometry()
            x1 = min(x1, x)
            x2 = max(x2, x)
            y1 = min(y1, y)
            y2 = max(y2, y)
        for link in self.links():
            vertices = link.get_vertices()
            for vertex in vertices:
                x, y = vertex[0:2]
                x1 = min(x1, x)
                x2 = max(x2, x)
                y1 = min(y1, y)
                y2 = max(y2, y)
        dx, dy = x2-x1, y2-y1
        x1, y1, x2, y2 = x1-0.1*dx, y1-0.1*dy, x2+0.1*dx, y2+0.1*dy

        # WRITE BACKDROP SECTION
        newsection = []
        for line in sections['BACKDROP']:
            # SERCH DIMENSIONS
            if 'DIMENSIONS' in line:
                newline = 'DIMENSIONS  {}  {}  {}  {}'.format(x1, y1, x2, y2)
            # BYPASS
            else:
                newline = line
            newsection.append(newline)
        sections['BACKDROP'] = newsection

        # WRITE EPANET INP FILE
        ERR_MSG = '; File generated automatically by Water Network Tools \n'
        sections['TITLE'].append(ERR_MSG)
        htext.write(inpf)
