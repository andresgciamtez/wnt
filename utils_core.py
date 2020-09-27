# -*- coding: utf-8 -*-

"""
/***************************************************************************
 WaterNetworkTools
                                 A QGIS plugin
 Water Network Modelling Utilities

                              -------------------
        begin                : 2019-07-19
        copyright            : (C) 2019 by Andrés García Martínez
        email                : ppnoptimizer@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Andrés García Martínez'
__date__ = '2019-07-19'
__copyright__ = '(C) 2019 by Andrés García Martínez'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from math import hypot
from .utils_parser import HeadedText, line_to_tuple, tuple_to_line

def length2d(linestring):
    '''Return the length of a line string.'''
    ERR_MSG = 'Bad geometry, it must be a list [(x, y) ...]'
    try:
        length = 0.0
        for i in range(len(linestring)-1):
            dx = linestring[i][0]-linestring[i+1][0]
            dy = linestring[i][1]-linestring[i+1][1]
            length += hypot(dx, dy)
        return length
    except:
        raise Exception(ERR_MSG)

def dist2p(point1, point2):
    '''Return the distance between to points (x1, x2), (x2, y2).'''
    ERR_MSG = 'point1, point2 must be a pair of (x, y) tuples.'
    try:
        return hypot(point1[0]-point2[0], point1[1]-point2[1])
    except:
        raise Exception(ERR_MSG)

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

    #  CHECK LINKS AND GET ENDS
    ERR_MSG1 = 'Zero length LineString.'
    ERR_MSG2 = 'Looped LineString.'
    ends = []
    for cnt, line in enumerate(linestrings):
        if length2d(line) == 0:
            raise Exception(ERR_MSG1)
        if dist2p(line[0], line[-1]) < tol:
            raise Exception(ERR_MSG2)
        ends.append((-(cnt + 1), line[0][0], line[0][1]))
        ends.append((cnt + 1, line[-1][0], line[-1][1]))

    # MERGE THE NODES
    ik = {}
    nodes = []
    ends.sort(key=lambda x: x[1], reverse=True)
    k = -1
    ncluster = Cluster()
    while ends:
        k += 1
        i, x, y = ends.pop(-1)
        ik[i] = k
        ncluster.add(x, y)
        if ends:
            offset = -1
            while -offset <= len(ends):
                i, x, y = ends[offset]
                if ncluster.x_dist(x) > tol:
                    break
                if ncluster.dist(x, y) <= tol:
                    ik[i] = k
                    ncluster.add(x, y)
                    ends.pop(offset)
                else:
                    offset -= 1
        nodes.append(ncluster.pop())

    # DISPLACE THE ENDS TO THE NODES
    links = []
    for cnt, line in enumerate(linestrings):
        start = ik[-(cnt + 1)]
        end = ik[cnt + 1]
        geometry = line[:]
        geometry[0] = nodes[start]
        geometry[-1] = nodes[end]
        links.append([start, end, geometry])

    return (nodes, links)

class Cluster:
    """Merge points generating nodes, (used for network_from_linestrings)."""
    def __init__(self):
        self._xCoor = []
        self._yCoor = []

    def add(self, x, y):
        """Add point."""
        self._xCoor.append(x)
        self._yCoor.append(y)

    def pop(self):
        """pop node and reset."""
        x = sum(self._xCoor)/len(self._xCoor)
        self._xCoor = []
        y = sum(self._yCoor)/len(self._yCoor)
        self._yCoor = []
        return (x, y)

    def x_dist(self, x):
        """Return the min distance to x."""
        return min((abs(x-x0) for x0 in self._xCoor))

    def dist(self, x, y):
        """Return the min distance to (x, y)."""
        tmp = zip(self._xCoor, self._yCoor)
        return min([(hypot(x-x0, y-y0)) for x0, y0 in tmp])


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
        if self._x and self._y:
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
        if length2d(linestring) == 0:
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
        return length2d(self._linestring)


class WntNetwork:
    """WntNetwork class."""
    def __init__(self):
        self._nodes = []
        self._links = []

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
        self._nodes.append(node)

    def node(self, index):
        """Return the node."""
        return self._nodes[index]

    def add_link(self, link):
        """Add a link to the network."""
        ERR_MSG = 'Bad type. Must be Node.'
        if not isinstance(link, WntLink):
            raise Exception(ERR_MSG)
        self._links.append(link)

    def link(self, index):
        """Return the link."""
        return self._links[index]

    def get_nodeindex(self, nodeid):
        """Return the index of the labeled node: nodeid, None  if not exists."""
        for index, node in enumerate(self._nodes):
            if node.name() == nodeid:
                return index

    def get_linkindex(self, linkid):
        """Return the index of the labeled link: linkid, None if not exists."""
        for index, link in enumerate(self._links):
            if link.name() == linkid:
                return index

    def from_lines(self, linestrings, **kwargs):
        """Build a network from lines trings.

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
        self._nodes = None
        self._links = None

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
            self.add_node(WntNode(node_id(index)))

        # ADD LINKS
        for index, start, end, linestring in enumerate(links):
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
        htext = HeadedText()
        htext.read(epanetf)
        sections = htext.sections

        # INPUT JUNCTIONS # ID Elev Demand Pattern
        for line in  sections['JUNCTIONS']:
            tmp = line_to_tuple(line)
            junction = WntNode(tmp[0])
            junction.set_type('JUNCTION')
            junction.set_elevation(tmp[1])
            self.add_node(junction)

        # INPUT RESERVOIRS # ID Head Pattern
        for line in sections['RESERVOIRS']:
            tmp = line_to_tuple(line)
            reservoir = WntNode(tmp[0])
            reservoir.set_type('RESERVOIR')
            reservoir.set_elevation = (tmp[1])
            self.add_node(reservoir)

        # INPUT TANKS # ID Elevation InitLevel MinLevel MaxLevel
        # Diameter MinVol VolCurve
        for line in  sections['TANKS']:
            tmp = line_to_tuple(line)
            tank = WntNode(tmp[0])
            tank.set_type('TANK')
            tank.set_elevation(tmp[1])
            self.add_node(tank)

        # COORDINATES
        for line in sections['COORDINATES']:
            nid, x, y = line_to_tuple(line)
            index = self.get_nodeindex(nid)
            self._nodes[index].set_geometry((float(x), float(y)))

        # INPUT PIPES # ID Node1 Node2 Length Diameter Roughness MinorLoss
        # Status
        for line in  sections['PIPES']:
            tmp = line_to_tuple(line)
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
        for line in  sections['PUMPS']:
            tmp = line_to_tuple(line)
            lid, n1, n2 = tmp[0:3]
            pump = WntLink(lid, n1, n2)
            pump.set_type('PUMP')
            self.add_link(pump)

        # INPUT VALVES # ID Node1 Node2 Diameter Type Setting MinorLoss
        for line in  sections['VALVES']:
            tmp = line_to_tuple(line)
            lid, n1, n2 = tmp[0:3]
            t = tmp[4]
            valve = WntLink(lid, n1, n2)
            valve.set_type(t)
            self.add_link(valve)

        # VERTICES
        for link in self.links():
            tmp = [self._nodes[self.get_nodeindex(link.start())].get_geometry()]
            tmp.append(self._nodes[self.get_nodeindex(link.end())].get_geometry())
            link.set_geometry(tmp)

        for line in sections['VERTICES']:
            nid, x, y = line_to_tuple(line)
            index = self.get_linkindex(nid)
            poly = self._links[index].get_geometry()
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
        htext = HeadedText()

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
                sections['JUNCTIONS'].append(tuple_to_line(tmp))

            if nodetype == 'RESERVOIR':
                if node.get_elevation():
                    tmp = (node.name(), node.get_elevation())
                else:
                    tmp = (node.name(), 0.0)
                sections['RESERVOIRS'].append(tuple_to_line(tmp))

            if nodetype == 'TANK':
                if node.get_elevation():
                    tmp = (node.name(), node.get_elevation(), 0.0, 0.0, 0.0, 0.0, 0.0)
                else:
                    tmp = (node.name(), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
                sections['TANKS'].append(tuple_to_line(tmp))

            x, y = node.get_geometry()
            line = tuple_to_line((node.name(), x, y))
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
                sections['PIPES'].append(tuple_to_line(tmp))

            elif linktype == 'PUMP':
                tmp = (link.name(), link.start(), link.end())
                sections['PUMPS'].append(tuple_to_line(tmp))

            elif linktype in ['PRV', 'PSV', 'PBV', 'FCV', 'TCV', 'GPV']:
                tmp = (link.linkid(), link.start(), link.end(), 0.0, linktype)
                tmp = tmp + (0.0, 0.0)
                sections['VALVES'].append(tuple_to_line(tmp))

            vertices = link.get_vertices()
            if vertices:
                for vertice in vertices:
                    tmp = (link.name(), vertice[0], vertice[1])
                    sections['VERTICES'].append(tuple_to_line(tmp))

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
        tgffile = open(fn, 'w')
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
        tgffile.close()

    def degree(self):
        """Return a dictionary, where: key: node id and value: node degree.
        """
        degrees = {}

        # CALCULATE DEGREE
        for node in self.nodes():
            degrees[node.name()] = 0
        for link in self.links():
            for linkend in [link.start(), link.end()]:
                degrees[linkend] += 1
        return degrees

    def validate(self):
        """Return the problems detected in the network.

        Analyse the network graph and retrieve a dictionary:
        where key, value are:
            'orphan nodes': set, orphan node IDs
            'duplicate nodes': set, duplicated node  IDs
            'undefined node links': set, undefined node link  IDs
            'duplicate links': set duplicate link IDs
            'loops': set, loopped link IDs
        """
        problems = {}

        # ORPHAN NODES
        ap = problems['orphan nodes'] = set()
        for node in self.nodes():
            ap.add(node.name())
        for link in self.links():
            ap.discard(link.start())
            ap.discard(link.end())

        # DUPLICATE NODE ID
        bp = problems['duplicate nodes'] = set()
        for index, nodei in enumerate(self.nodes()[:-1]):
            for nodej in self.nodes()[index+1:]:
                if nodei.name() == nodej.name():
                    bp.add(nodei.name())
                    break

        # UNDEFINED LINK START OR END NODES
        cp = problems['undefined node links'] = set()
        ep = problems['loops'] = set()
        def exits_node(name):
            return isinstance(self.get_nodeindex(name), int)

        for link in self.links():
            for nodeid in [link.start(), link.end()]:
                if not exits_node(nodeid) and nodeid not in ap:
                    cp.add(link.name())
                    break

            # START NODE ID = END NODE ID. LOOP
            if link.start() == link.end():
                ep.add(link.name())

        # DUPLICATE LINK ID
        dp = problems['duplicate links'] = set()
        for index, linki in enumerate(self.links()[:-1]):
            for linkj in self.links()[index+1:]:
                if linki.name() == linkj.name():
                    dp.add(linki.name())
        return problems
