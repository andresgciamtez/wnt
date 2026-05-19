"""Core network model and EPANET file helpers."""

from collections import defaultdict
from itertools import pairwise
from math import dist, floor
from .parser import SectionedText, format_tokens, parse_tokens


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
    NODE_TYPES = ['JUNCTION', 'RESERVOIR', 'TANK']

    def __init__(self, name):
        # ERR_MSG = 'Name too long. MAX LEN = {}.'.format(WntNode.MAX_NAME_LEN)
        # if len(name) > WntNode.MAX_NAME_LEN:
        #     raise Exception(ERR_MSG)
        self._name = name
        self._x = None
        self._y = None
        self._elevation = None
        self._type = None

    def __str__(self):
        return 'WntNode: {}.'.format(self._name)

    def name(self):
        """Return name (epanet ID)."""
        return self._name

    def set_geometry(self, coor):
        """Set node geometry where coor is a float tuple (x, y)."""
        ERR_MSG = 'Bad geometry, it must be a (x, y) float tuple.'
        try:
            self._x = float(coor[0])
            self._y = float(coor[1])
        except:
            raise Exception(ERR_MSG)

    def get_geometry(self):
        """Get node geometry as a float tuple (x, y)."""
        return (self._x, self._y)

    def set_elevation(self, z):
        """Set node elevation."""
        ERR_MSG = 'Bad elevation.'
        try:
            self._elevation = float(z)
        except:
            raise Exception(ERR_MSG)

    def get_elevation(self):
        """Get node elevation."""
        return self._elevation

    def set_type(self, nodetype):
        """Set node type."""
        ERR_MSG = 'Incorrect type, it must be: {}.'.format(WntNode.NODE_TYPES)
        try:
            self._type = nodetype.upper()
        except:
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
        except:
            raise Exception(ERR_MSG)

    def to_wkt(self):
        """Return the node geometry in WKT format, 'Point (x y).'"""
        if self._x is not None and self._y is not None:
            return 'Point({} {})'.format(self._x, self._y)


class WntLink:
    """WntLink class."""

    MAX_NAME_LEN = 15
    LINK_TYPES = ['PIPE', 'CVPIPE', 'PUMP', 'PRV', 'PSV', 'PBV', 'FCV',
                  'TCV', 'GPV']

    def __init__(self, name, start, end):
        # ERR_MSG = 'Name too long. MAX LEN = {}.'.format(WntNode.MAX_NAME_LEN)
        # if max([len(str(n)) for n in [name, start, end]]) > WntNode.MAX_NAME_LEN:
        #     raise Exception(ERR_MSG)
        self._name = name
        self._start = start
        self._end = end
        self._linestring = None
        self._type = None
        self.epanet = {}

    def __str__(self):
        ERR_MSG = 'WntLink: {}. {} -> {}.'
        return ERR_MSG.format(self._name, self._start, self._end)

    def name(self):
        """Return name (epanet ID)."""
        return self._name

    def start(self):
        """Return the link start (node name)."""
        return self._start

    def end(self):
        """Return the link end (node name)."""
        return self._end

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
        except:
            raise Exception(ERR_MSG3)
        if polyline_length(linestring) == 0:
            self._linestring = None
            raise Exception(ERR_MSG4)

    def get_geometry(self):
        """Return link geometry as a list of coordinate tuples [(x, y) ...]."""
        return self._linestring

    def get_startpoint(self):
        """Return the initial point coordinates."""
        if self._linestring:
            return self._linestring[0]

    def get_endpoint(self):
        """Return the final point coordinates."""
        if self._linestring:
            return self._linestring[-1]

    def get_vertices(self):
        """Return the middle vertices."""
        if self._linestring:
            return self._linestring[1:-1]

    def set_type(self, linktype):
        """Set link type."""
        ERR_MSG = 'Bad type, it must be: {}'.format(WntLink.LINK_TYPES)
        try:
            linktype = linktype.upper()
            self._type = linktype
        except:
            raise Exception(ERR_MSG)
        if self._type not in WntLink.LINK_TYPES:
            del self._type
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
        except:
            raise Exception(ERR_MSG1)
        if 'MULTI' in txt:
            raise Exception(ERR_MSG2)
        try:
            for clean in ['LINESTRING', 'Z', '(', ')', '"', '\n']:
                txt = txt.replace(clean, '')
            points = []
            for point in  txt.strip().split(','):
                point = point.strip().split(' ')
                points.append((float(point[0]), float(point[1])))
        except:
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

    def length(self):
        """Return the link length."""
        return polyline_length(self._linestring)


class WntNetwork:
    """WntNetwork class."""
    def __init__(self):
        self._nodes = []
        self._links = []
        self._node_map = {} # name -> index
        self._link_map = {} # name -> index

    def __str__(self):
        return 'WntNetwork.'

    def nodes(self):
        """Return the network nodes"""
        return self._nodes

    def links(self):
        """Return the network links"""
        return self._links

    def add_node(self, node):
        """Add a node to the network."""
        ERR_MSG = 'Bad type. Must be Node.'
        if not isinstance(node, WntNode):
            raise Exception(ERR_MSG)
        if node.name() not in self._node_map:
            self._node_map[node.name()] = len(self._nodes)
        self._nodes.append(node)

    def node(self, index):
        """Return the node."""
        return self._nodes[index]

    def add_link(self, link):
        """Add a link to the network."""
        ERR_MSG = 'Bad type. Must be Node.'
        if not isinstance(link, WntLink):
            raise Exception(ERR_MSG)
        if link.name() not in self._link_map:
            self._link_map[link.name()] = len(self._links)
        self._links.append(link)

    def link(self, index):
        """Return the link."""
        return self._links[index]

    def get_nodeindex(self, nodeid):
        """Return the index of the labeled node: nodeid, None  if not exists."""
        return self._node_map.get(nodeid)

    def get_linkindex(self, linkid):
        """Return the index of the labeled link: linkid, None if not exists."""
        return self._link_map.get(linkid)

    def from_lines(self, linestrings, **kwargs):
        """Build a network from line strings.

        Parameters
        ----------
        linestring: listrings, [(x, y), ..]. A list of (x, y) points

        **kwargs
        tol: float, fusion distance, default 0.0
        nmask: str, mask of nodes ID prefix$$$suffix, default = ''
        nini: int, node numbering start, default = 0
        ninc: int, node numbering increment, default = 1
        lmask: str, mask of link ID prefix$$$suffix, default = ''
        lini: int, link numbering start, default = 0
        linc: int, link numbering increment, , default = 1
        """

        # CLEAR
        self._nodes = []
        self._links = []
        self._node_map = {}
        self._link_map = {}

        # CONFIG
        f = lambda k, d: kwargs[k] if k in kwargs else d

        tol = f('tol', 0.0)

        def node_id(index):
            return format_id(f('nini', 0) + index*f('ninc', 1), f('nmask', ''))

        def link_id(index):
            return format_id(f('lini', 0) + index*f('linc', 1), f('lmask', ''))

        # CALCULATE NETWORK
        nodes, links = net_from_linestrings(linestrings, tol)

        # ADD NODES
        for index, coordinates in enumerate(nodes):
            node = WntNode(node_id(index))
            node.set_geometry(coordinates)
            self.add_node(node)

        # ADD LINKS
        for index, (start, end, linestring) in enumerate(links):
            link = WntLink(link_id(index), node_id(start), node_id(end))
            link.set_geometry(linestring)
            self.add_link(link)

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
            self.add_node(junction)

        # INPUT RESERVOIRS # ID Head Pattern
        for line in sections.get('RESERVOIRS', []):
            tmp = parse_tokens(line)
            reservoir = WntNode(tmp[0])
            reservoir.set_type('RESERVOIR')
            reservoir.set_elevation(tmp[1])
            self.add_node(reservoir)

        # INPUT TANKS # ID Elevation InitLevel MinLevel MaxLevel
        # Diameter MinVol VolCurve
        for line in  sections.get('TANKS', []):
            tmp = parse_tokens(line)
            tank = WntNode(tmp[0])
            tank.set_type('TANK')
            tank.set_elevation(tmp[1])
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
            self.add_link(pipe)

        # INPUT PUMPS #  # ID Node1 Node2 Parameters
        for line in  sections.get('PUMPS', []):
            tmp = parse_tokens(line)
            lid, n1, n2 = tmp[0:3]
            pump = WntLink(lid, n1, n2)
            pump.set_type('PUMP')
            self.add_link(pump)

        # INPUT VALVES # ID Node1 Node2 Diameter Type Setting MinorLoss
        for line in  sections.get('VALVES', []):
            tmp = parse_tokens(line)
            lid, n1, n2 = tmp[0:3]
            t = tmp[4]
            valve = WntLink(lid, n1, n2)
            valve.set_type(t)
            self.add_link(valve)

        # VERTICES
        for link in self.links():
            start_index = self.get_nodeindex(link.start())
            end_index = self.get_nodeindex(link.end())
            if start_index is None or end_index is None:
                continue
            tmp = [self._nodes[start_index].get_geometry()]
            tmp.append(self._nodes[end_index].get_geometry())
            link.set_geometry(tmp)

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
            # (id,start,end, ...
            tmp = (link.name(), link.start(), link.end())
            if linktype in ['PIPE', 'CVPIPE'] or not linktype:
                # length,diameter,roughness,minorLoss, ...
                if 'length' in link.epanet:
                    tmp = tmp + (link.epanet['length'], 0.0, 0.0, 0.0)
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

    def to_tgf(self, fn):
        """Export network topology to Trivial Graph Format (TGF)"""

        # OPEN AND SAVE NODES
        with open(fn, 'w', encoding='utf-8') as tgffile:
            for index, node in enumerate(self.nodes()):
                tgffile.write('{} {} \n'.format(index, node.name()))
            tgffile.write('# \n')

            # SAVE EDGES AND CLOSE
            for link in self.links():
                txt = '{} {} {} \n'
                sindex = self.get_nodeindex(link.start())
                eindex = self.get_nodeindex(link.end())
                txt = txt.format(sindex, eindex, link.name())
                tgffile.write(txt)

    def degree(self):
        """Return a dictionary, where: key: node id and value: node degree.
        """
        degrees = {}

        # CALCULATE DEGREE
        for node in self.nodes():
            degrees[node.name()] = 0
        for link in self.links():
            for linkend in [link.start(), link.end()]:
                if linkend not in degrees:
                    degrees[linkend] = 0
                degrees[linkend] += 1
        return degrees

    def validate(self):
        """Return the problems detected in the network.

        Analyse the network graph and retrieve a dictionary:
        where key, value are:
            'orphan nodes': set, orphan node IDs
            'duplicate nodes': set, duplicated node IDs
            'undefined node links': set, undefined node link IDs
            'duplicate links': set duplicate link IDs
            'loops': set, looped link IDs
        """
        problems = {
            'orphan nodes': set(),
            'duplicate nodes': set(),
            'undefined node links': set(),
            'duplicate links': set(),
            'loops': set()
        }

        # NODE CHECKS
        seen_nodes = set()
        for node in self.nodes():
            name = node.name()
            if name in seen_nodes:
                problems['duplicate nodes'].add(name)
            seen_nodes.add(name)
            problems['orphan nodes'].add(name)

        # LINK CHECKS
        seen_links = set()
        for link in self.links():
            name = link.name()
            # Duplicate ID
            if name in seen_links:
                problems['duplicate links'].add(name)
            seen_links.add(name)

            # Orphan/Undefined
            start_name = link.start()
            end_name = link.end()

            problems['orphan nodes'].discard(start_name)
            problems['orphan nodes'].discard(end_name)

            if start_name not in seen_nodes:
                problems['undefined node links'].add(name)
            elif end_name not in seen_nodes:
                problems['undefined node links'].add(name)

            # Loops
            if start_name == end_name:
                problems['loops'].add(name)

        return problems
