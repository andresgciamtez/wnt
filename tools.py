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

from math import copysign
from os.path import exists as fexits
import csv
from . import htxt


def dist_2_p(point1, point2):
    """Return the distance, 2D, between 2 points, (x1,y1) and (x2,y2)."""

    #CHECK TYPES
    msg = 'Incorrect point format, it must be use 2 tuples (x y).'
    assert isinstance(point1, tuple) and  isinstance(point2, tuple), msg

    # PERFORM CALCULATION
    return ((point1[0]-point2[0])**2+((point1[1]-point2[1])**2))**0.5

def split_linestring(linestring, point, tolerance=0.0):
    """Return the splitted linestring by the intersecting point. The result is:

    If intersection exists, a tuple containing the two parts:
        (fpart, spart), where:
        fpart = [initial_point, ..., point]
        spart = [point, ..., end_point]
    Otherwwise return None.

    Arguments
    ---------
    linestring: list, containing the linestring vertices (x,y) as tuples
    point: tuple, the splitting point coordinates (x,y)
    """

    # CHECK TYPES
    assert isinstance(linestring, list), 'Linestring is not a list.'
    assert isinstance(point, tuple), 'Point is not a tuple.'


    # SPLIT LINESTRING
    # SEGMENT LOOP
    n = len(linestring)-1
    for i in range(n):
        xs, ys = linestring[i][0:2]
        x1e, y1e = linestring[i+1][0]-xs, linestring[i+1][1]-ys
        x1p, y1p = point[0]-xs, point[1]-ys
        cteta = x1e / (x1e**2 + y1e**2)**0.5
        steta = copysign((1-cteta**2)**0.5, y1e)
        b = x1e*cteta + y1e*steta
        d = -x1p*steta + y1p*cteta
        a = x1p*cteta + y1p*steta
        xi = xs + a*cteta
        yi = ys + a*steta
#        from math import acos, pi
#        print(180*acos(cteta)/pi)
#        print('Cos(teta) =', cteta)
#        print('Sin(teta) =', steta)
#        print('a =', a)
#        print('b =', b)
#        print('d =', d)
#        print ('xi =', xi, 'yi =', yi)

        # IGNORE TOO SHORT SEGMENT
        if b > tolerance:
            # DETECT PROXIMITY
            if abs(d) <= tolerance:
                if -tolerance <= a <= tolerance:
                    if i == 0:
                        print('Near start point')
                        return None # IGNORE INTERSECTION AT START POINT
                    # SPLIT AT INITIAL SEGMENT POINT
                    print('Splitted at vertex')
                    fpart = linestring[0:i+2].copy()
                    spart = linestring[i+1:].copy()
                    return (fpart, spart)
                if b-tolerance <= a <= b+tolerance:
                    if i == n-1:
                        print('Near end point')
                        return None # IGNORE INTERSECTION AT END POINT
                    # SPLIT AT FINAL SEGMENT POINT
                    print('Splitted at vertex')
                    fpart = linestring[0:i+2].copy()
                    spart = linestring[i+1:].copy()
                    return(fpart, spart)
                if tolerance < a < b-tolerance:
                    # SPLIT AT SEGMENT
                    print('Splitted at inner point')
                    fpart = linestring[0:i+1].copy()
                    fpart.append((xi, yi))
                    spart = linestring[i+1:].copy()
                    spart.insert(0, (xi, yi))
                    return (fpart, spart)
        else:
            print('Too short segment')
    # SPLITTING POINT NOT FOUND
    return None

def split_linestring_m(linestring, points, tolerance=0.0):
    """Return a list of linestring parts splitted by points.

    The result is a list of list containing the linestring parts.
    [[initial_point, ..., first_division], ..., [last_division, final_point]]

    Arguments
    ---------
    linestring: list, containing the linestring vertices (x,y) as tuples
    points: list, containing a list of points (x,y) as tuples
    """
    assert isinstance(linestring, list), 'Linestring is not a list.'
    assert isinstance(points, list), 'Points is not a list.'

    # INITIALIZE RESULT LINES
    result = [linestring.copy()]

    # POINTS LOOP
    for point in points:

        # LINESTRINGS LOOP
        for index, line in enumerate(result):
            # SPLIT
            splitted = split_linestring(line, point, tolerance)

            # CHANGE OLD LINE AND ADD NEW
            if splitted:
                result[index] = splitted[0]
                result.insert(index+1, splitted[1])
                break

    # RETURN RESULT
    return result


class Node:
    """Node class."""
    def __init__(self, nodeid):
        self.nodeid = nodeid
        self._type = None
        self._x = None
        self._y = None
        self.elevation = None

    def set_geometry(self, coor):
        """Set node geometry where coor is a float tuple (x, y)."""
        msg = 'Incorrect node geometry, it must be a (x, y) tuple.'
        assert isinstance(coor, tuple), msg
        assert isinstance(coor[0], float) and isinstance(coor[1], float), msg
        self._x, self._y = coor[:2]

    def get_geometry(self):
        """Get node geometry as a float tuple (x, y)."""
        if isinstance(self._x, float) and isinstance(self._y, float):
            return self._x, self._y
        return None

    def set_type(self, nodetype):
        """Set node type 'JUNCTION'/'RESERVOIR'/'TANK."""
        msg = 'Incorrect node type, it must be: JUNCTION/RESERVOIR/TANK.'
        nodetype = nodetype.upper()
        assert nodetype in ('JUNCTION', 'RESERVOIR', 'TANK'), msg
        self._type = nodetype

    def get_type(self):
        """Get node type if it is defined, otherwise None."""
        if self._type:
            return self._type
        return None

    def from_wkt(self, wkt):
        """Set geometry from a WKT format point, 'Point (x y).'"""
        msg = "Incorrect WKT point format, it must be 'Point (x y).'"
        assert isinstance(wkt, str), msg
        point = wkt.upper()
        for s in ['POINT', 'Z', '(', ')', '"', '\n']:
            point = point.replace(s, '')
        point = point.strip().split()
        point = float(point[0]), float(point[1])
        self.set_geometry(point)

    def to_wkt(self):
        """Return the node geometry in WKT format, 'Point (x y).'"""
        msg = 'Not defined/error in node coordinates.'
        assert isinstance(self._x, float) and isinstance(self._y, float), msg
        return 'Point ({} {})'.format(self._x, self._y)

    def __str__(self):
        txt = 'Node: {}. Type: {}.'.format(self.nodeid, self.get_type())
        return txt


class Link:
    """Link class."""
    def __init__(self, linkid, start, end):
        self.linkid = linkid
        self.start = start
        self.end = end
        self._type = None
        self._linestring = None
        self.length = None
        self.diameter = None
        self.roughness = None

    def set_geometry(self, linestring):
        """Set link geometry as a list of coordinate tuples [(x, y) ...]."""
        msg = 'Incorrect geometry, it must be a list of tuples [(x,y) ...].'
        assert isinstance(linestring, list), msg
        msg = 'Not enough vertices, it must be specified 2 or more.'
        assert len(linestring) > 1, msg
        msg = 'Incorrect vertex format it must be a float tuple (x, y).'
        for vertex in linestring:
            assert isinstance(vertex[0], float), msg
            assert isinstance(vertex[1], float), msg
        self._linestring = linestring

    def get_geometry(self):
        """Return link geometry as a list of coordinate tuples [(x, y) ...]."""
        return self._linestring

    def get_startpoint(self):
        """Return the initial point coordinates."""
        if self._linestring:
            return self._linestring[0]
        return None # Not defined geometry

    def get_endpoint(self):
        """Return the final point coordinates."""
        if self._linestring:
            return self._linestring[-1]
        return None # Not defined geometry

    def get_vertices(self):
        """Return the middle vertices."""
        if self._linestring:
            return self._linestring[1:-1]
        return None # Not defined geometry

    def set_type(self, linktype):
        """Set link type PIPE/CVPIPE/PUMP/PRV/PSV/PBV/FCV/TCV/GPV."""
        msg = 'Incorrect link type, it must be: '
        msg += 'PIPE/CVPIPE/PUMP/PRV/PSV/PBV/FCV/TCV/GPV.'
        assert isinstance(linktype, str), msg
        linktypes = ['PIPE', 'CV', 'PUMP', 'PRV', 'PSV', 'PBV', 'FCV', 'TCV', \
                     'GPV']
        linktype = linktype.upper()
        assert linktype in linktypes, msg
        self._type = linktype

    def get_type(self):
        """Get link type if it is defined, otherwise None."""
        if self._type:
            return self._type
        return None

    def from_wkt(self, wkt):
        """Set the geometry from a WKT format line, 'LineString (x y, ...)'."""
        msg = "Incorrect WKT format, it must be 'LineString (x y, ...).'"
        assert isinstance(wkt, str), msg
        points = wkt.upper()
        assert not ('MULTI' in wkt), 'Multi-geometry is not supported.'
        for s in ['LINESTRING', 'Z', '(', ')', '"', '\n']:
            points = points.replace(s, '')
        points = points.strip().split(',')
        assert len(points) > 1, 'It must be specified 2 or more points.'
        linestring = []
        for point in points:
            point = point.split()[0:2]
            assert len(point) > 1, msg
            x, y = float(point[0]), float(point[1])
            linestring.append((x, y))
        self.set_geometry(linestring)

    def to_wkt(self):
        """Return the node geometry in WKT format. 'LineString (x y, ...)'."""
        if self._linestring:
            tmp = 'LineString ('
            for point in self._linestring[0:-1]:
                tmp += str(point[0]) + ' ' + str(point[1]) + ','
            point = self._linestring[-1]
            return tmp + str(point[0]) + ' ' + str(point[1]) + ')'
        return None # Not defined geometry

    def length2d(self):
        '''Return the 2D length of the link.'''
        pol = self.get_geometry()
        assert isinstance(pol, list), 'Not defined geometry.'
        length = 0.0
        for i in range(len(pol)-1):
            dx = pol[i][0]-pol[i+1][0]
            dy = pol[i][1]-pol[i+1][1]
            length += (dx**2+dy**2)**0.5
        return length


class Network:
    """Main class. A network represented by two lists: nodes and links."""
    def __init__(self):
        self.nodes = []
        self.links = []

    def __str__(self):
        txt = 'Network. Nodes: {}. Links: {}.'
        txt = txt.format(len(self.nodes), len(self.links))
        return txt

    def get_nodeindex(self, nodeid):
        """Return the index of the labeled node: nodeid, None  if not exists."""
        for index in range(len(self.nodes)):
            if self.nodes[index].nodeid == nodeid:
                return index
        return None # if node not exit

    def get_linkindex(self, linkid):
        """Return the index of the labeled link: linkid, None if not exists."""
        for index in range(len(self.links)):
            if self.links[index].linkid == linkid:
                return index
        return None # if link not exit

    def from_lines(self, lines, t=0.0, prefixnode='Node-', nodeinit=0, \
                   nodedelta=1, prefixlink='Link-', firstlink=0, linkdelta=1):
        """Make a network (geometry and topology) from txt lines in WKT format.

        Parameters
        ----------
        lines: list, containing txt lines geometry as WKT (LineString)
        t: float, nodes separated lesser than t are merged
        prefixnode: str, prefix of the nodes
        firstnode: int, number of the first node
        deltanode: int, increment of the node number
        prefixlink: str, prefix of the links
        firstlink: int, number of the first link
        linkdelta: int, increment of the number link
        """
        # LOAD LINKS
        links = []
        linkcnt = 0

        for line in lines:
            if 'LINESTRING' in line.upper():
                linkid = prefixlink + str(firstlink + linkdelta*linkcnt)
                newlink = Link(linkid, linkcnt*2, linkcnt*2+1)
                newlink.set_type('PIPE')
                newlink.from_wkt(line)
                links.append(newlink)
                linkcnt += 1

        # REDUCING OVERLAPPED POINTS
        usednodes = set()
        cnt = 0
        for i in range(len(links)):
            assert links[i].length2d() >= 2*t, 'Too short link.'
            if not links[i].start in usednodes:
                links[i].start = cnt
                usednodes.add(cnt)
                cnt += 1

            if not links[i].end in usednodes:
                links[i].end = cnt
                usednodes.add(cnt)
                cnt += 1

            point1 = links[i].get_startpoint()
            point2 = links[i].get_endpoint()

            # MERGE
            for j in range(i+1, len(links)):
                point3 = links[j].get_startpoint()
                point4 = links[j].get_endpoint()
                if dist_2_p(point3, point1) <= t:
                    links[j].start = links[i].start

                elif dist_2_p(point4, point1) <= t:
                    links[j].end = links[i].start

                if dist_2_p(point3, point2) <= t:
                    links[j].start = links[i].end

                elif dist_2_p(point4, point2) <= t:
                    links[j].end = links[i].end

        # AVERAGE COORDINATES
        avgcoor = {}
        for link in links:
            if link.start in avgcoor:
                avgcoor[link.start].append(link.get_startpoint())
            else:
                avgcoor[link.start] = [link.get_startpoint()]

            if link.end in avgcoor:
                avgcoor[link.end].append(link.get_endpoint())
            else:
                avgcoor[link.end] = [link.get_endpoint()]

        for key in avgcoor:
            n = len(avgcoor[key])
            x, y = 0, 0
            for coor in avgcoor[key]:
                x += coor[0]
                y += coor[1]
            avgcoor[key] = (x/n, y/n)

        # CREATE NODES
        nodes = []
        rename = {}
        for key in avgcoor:
            nodeid = prefixnode + str(nodeinit + nodedelta * key)
            rename[key] = nodeid
            mynode = Node(nodeid)
            mynode.set_geometry(avgcoor[key])
            mynode.elevation = 0.0
            nodes.append(mynode)

        # UPDATE LINKS
        for link in links:
            link.start = rename[link.start]
            link.end = rename[link.end]

        # UPDATE LENGTH
        for link in links:
            link.length = link.length2d()

        # UPDATE NETWORK
        self.nodes = nodes
        self.links = links

    def from_csv(self, nodescsv, linkscsv):
        """Import a network from geocsv data.'

        Node data: id, geometry [, type, elevation]
        Link data: id, start, end, geometry [,type]

        Parameters
        ----------
        nodescsv: file name, input node file in geocsv format
        linkscsv: file name, input link file in geocsv format
        """
        # READ NODES FILE AND UPDATING NETWORK
        assert fexits(nodescsv), 'I cannot find file: ' + nodescsv
        with open(nodescsv, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)  # read rows into a dictionary format
            msg = 'node id cannot be found  in nodes file'
            assert 'id' in reader.fieldnames, msg
            msg = 'geometry  cannot be found  in nodes file'
            assert 'geometry' in reader.fieldnames, msg
            for row in reader:
                newnode = Node(row['id'])
                newnode.from_wkt(row['geometry'])
                if 'type' in reader.fieldnames:
                    if row['type'] in ['JUNCTION', 'RESERVOIR', 'TANK']:
                        newnode.set_type(row['type'])

                if 'elevation' in reader.fieldnames:
                    newnode.elevation = row['elevation']

                #  IT IS PENDING TO IMPLEMENT THE REST OF PARAMETERS !

                # ADD NEW NODE
                self.nodes.append(newnode)

        # READ LINKS FILE AND UPDATING NETWORK
        assert fexits(linkscsv), 'I cannot find file: ' + linkscsv
        linktypes = ['PIPE', 'PUMP', 'PRV', 'PSV', 'PBV', 'FCV', 'TCV', 'GPV']
        with open(linkscsv, encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)  # read rows into a dictionary format
            msg = 'link id cannot be found  in nodes file'
            assert 'id' in reader.fieldnames, msg
            msg = 'link start/end cannot be found  in nodes file'
            assert 'start' in reader.fieldnames, msg
            assert 'end' in reader.fieldnames, msg
            msg = 'geometry  cannot be found  in nodes file'
            assert 'geometry' in reader.fieldnames, msg
            for row in reader:          # read a row as {column1: value1, ...}
                newlink = Link(row['id'], row['start'], row['end'])
                newlink.from_wkt(row['geometry'])
                if 'type' in reader.fieldnames:

                    if row['type'] in linktypes:
                        newlink.set_type(row['type'])
                    else:
                        newlink.set_type('PIPE')

                #  IT IS PENDING TO IMPLEMENT THE REST OF PARAMETERS !

                # ADD NEW LINK
                self.links.append(newlink)

    def nodes_to_geocsv(self, fn):
        """Export nodes to geoCSV format."""
        with open(fn, encoding='utf-8-sig', mode='w') as csvfile:
            fields = ['geometry', 'id', 'type', 'elevation']

            writer = csv.DictWriter(csvfile, fields)
            writer.writeheader()
            for node in self.nodes:
                nodeDic = {'geometry': node.to_wkt(),  \
                           'id': node.nodeid,           \
                           'type': node.get_type(),     \
                           'elevation': node.elevation  \
                           }
                writer.writerow(nodeDic)

    def links_to_geocsv(self, fn):
        """Export links in geoCSV format."""
        with open(fn, encoding='utf-8-sig', mode='w') as csvfile:
            fields = ['geometry', 'id', 'start', 'end', 'type', 'length']
            writer = csv.DictWriter(csvfile, fields)
            writer.writeheader()
            for link in self.links:
                nodeDic = {'geometry': link.to_wkt(),  \
                           'id': link.linkid,           \
                           'start': link.start,         \
                           'end': link.end,             \
                           'type': link.get_type(),     \
                           'length': link.length        \
                           }
                writer.writerow(nodeDic)

    def from_epanet(self, epanetfn):
        """Make a network from a epanet file, reading:

        Node data: id, type, elevation and coordinates.
        Nink data: id, type, start, end, type, vertices.

        IT IS PENDING TO IMPLEMENT THE REST OF PARAMETERS !

        Parameters
        ----------
        epanetfn: epanet file name (*.inp), input epanet model
        """
        # READ EPANET FILE
        htxtfile = htxt.Htxtf()
        htxtfile.read(epanetfn)
        sections = htxtfile.sections

        # INPUT JUNCTIONS # ID Elev Demand Pattern
        for line in  sections['JUNCTIONS']:
            tmp = htxt.line_to_tuple(line)
            junction = Node(tmp[0])
            junction.set_type('JUNCTION')
            junction.elevation = tmp[1]
            self.nodes.append(junction)

        # INPUT RESERVOIRS # ID Head Pattern
        for line in sections['RESERVOIRS']:
            tmp = htxt.line_to_tuple(line)
            reservoir = Node(tmp[0])
            reservoir.set_type('RESERVOIR')
            reservoir.elevation = tmp[1]
            self.nodes.append(reservoir)

        # INPUT TANKS # ID Elevation InitLevel MinLevel MaxLevel
        # Diameter MinVol VolCurve
        for line in  sections['TANKS']:
            tmp = htxt.line_to_tuple(line)
            tank = Node(tmp[0])
            tank.set_type('TANK')
            tank.elevation = tmp[1]
            self.nodes.append(tank)

        # COORDINATES
        for line in sections['COORDINATES']:
            nid, x, y = htxt.line_to_tuple(line)
            index = self.get_nodeindex(nid)
            self.nodes[index].set_geometry((float(x), float(y)))

        # INPUT PIPES # ID Node1 Node2 Length Diameter Roughness MinorLoss
        # Status
        for line in  sections['PIPES']:
            tmp = htxt.line_to_tuple(line)
            lid, n1, n2 = tmp[0:3]
            s = tmp[-1]
            pipe = Link(lid, n1, n2)
            if s == "CV":
                pipe.set_type('CVPIPE')
            else:
                pipe.set_type('PIPE')

            pipe.length = tmp[3]
            pipe.diameter = tmp[4]
            pipe.roughness = tmp[5]
            self.links.append(pipe)

        # INPUT PUMPS #  # ID Node1 Node2 Parameters
        for line in  sections['PUMPS']:
            tmp = htxt.line_to_tuple(line)
            lid, n1, n2 = tmp[0:3]
            pump = Link(lid, n1, n2)
            pump.set_type('PUMP')
            self.links.append(pump)

        # INPUT VALVES # ID Node1 Node2 Diameter Type Setting MinorLoss
        for line in  sections['VALVES']:
            tmp = htxt.line_to_tuple(line)
            lid, n1, n2 = tmp[0:3]
            t = tmp[4]
            valve = Link(lid, n1, n2)
            valve.set_type(t)
            self.links.append(valve)

        # VERTICES
        for link in self.links:
            tmp = [self.nodes[self.get_nodeindex(link.start)].get_geometry()]
            tmp.append(self.nodes[self.get_nodeindex(link.end)].get_geometry())
            link.set_geometry(tmp)

        for line in sections['VERTICES']:
            nid, x, y = htxt.line_to_tuple(line)
            index = self.get_linkindex(nid)
            poly = self.links[index].get_geometry()
            poly.insert(-1, (float(x), float(y)))

    def to_epanet(self, inpfname, tplfname):
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
        inpfname: str, output epanet file name (*.inp)
        tplfname: str, input template epanet file name (*.inp)
        """

        # READ EPANET FILE TEMPLATE
        outf = htxt.Htxtf()

        # LOAD TEMPLATE
        outf.read(tplfname)
        sections = outf.sections

        # ADD NODES/COORDINATES TO SECTION
        for node in self.nodes:
            nodetype = node.get_type()
            if nodetype == 'JUNCTION':
                if node.elevation:
                    tmp = (node.nodeid, node.elevation, 0.0)
                else:
                    tmp = (node.nodeid, 0.0, 0.0)
                sections['JUNCTIONS'].append(htxt.tuple_to_line(tmp))

            if nodetype == 'RESERVOIR':
                if node.elevation:
                    tmp = (node.nodeid, node.elevation)
                else:
                    tmp = (node.nodeid, 0.0)
                sections['RESERVOIRS'].append(htxt.tuple_to_line(tmp))

            if nodetype == 'TANK':
                if node.elevation:
                    tmp = (node.nodeid, node.elevation, 0.0, 0.0, 0.0, 0.0, 0.0)
                else:
                    tmp = (node.nodeid, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
                sections['TANKS'].append(htxt.tuple_to_line(tmp))

            x, y = node.get_geometry()
            line = htxt.tuple_to_line((node.nodeid, x, y))
            sections['COORDINATES'].append(line)

        # ADD LINKS/VERTICES TO SECTION
        for link in self.links:
            linktype = link.get_type()
            # (id,start,end, ...
            tmp = (link.linkid, link.start, link.end)
            if linktype in ['PIPE', 'CVPIPE'] or not linktype:
                # length,diameter,roughness,minorLoss, ...
                tmp = tmp + (link.length, 0.0, 0.0, 0.0)

                # status)
                if linktype == 'CVPIPE':
                    tmp = tmp + ('CV',)
                else:
                    tmp = tmp + ('Open',)
                sections['PIPES'].append(htxt.tuple_to_line(tmp))

            elif linktype == 'PUMP':
                tmp = (link.linkid, link.start, link.end)
                sections['PUMPS'].append(htxt.tuple_to_line(tmp))

            elif linktype in ['PRV', 'PSV', 'PBV', 'FCV', 'TCV', 'GPV']:
                tmp = (link.linkid, link.start, link.end, 0.0, linktype)
                tmp = tmp + (0.0, 0.0)
                sections['VALVES'].append(htxt.tuple_to_line(tmp))

            vertices = link.get_vertices()
            if vertices:
                for vertice in vertices:
                    tmp = (link.linkid, vertice[0], vertice[1])
                    sections['VERTICES'].append(htxt.tuple_to_line(tmp))

        # RESIZE [BACKDROP]
        x1, y1, x2, y2 = 1e12, 1e12, -1e12, -1e12
        for node in self.nodes:
            x, y = node.get_geometry()
            x1 = min(x1, x)
            x2 = max(x2, x)
            y1 = min(y1, y)
            y2 = max(y2, y)
        for link in self.links:
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
        msg = '; File generated automatically by Water Network Tools \n'
        sections['TITLE'].append(msg)
        outf.write(inpfname)

    def to_tgf(self, fn):
        """Export network topology to Trivial Graph Format (TGF)"""
        tgffile = open(fn, 'w')

        for node in self.nodes:
            index = self.get_nodeindex(node.nodeid)
            tgffile.write('{} {} \n'.format(index, node.nodeid))

        tgffile.write('# \n')

        for link in self.links:
            start = self.get_nodeindex(link.start)
            end = self.get_nodeindex(link.end)
            tgffile.write('{} {} {} \n'.format(start, end, link.linkid))

        tgffile.close()

    def validate(self):
        """Return the problems detected in the network.

        Analyse the network graph and retrieve: (onodes, dnodes, dlinks, unodes)
        onodes: set, the orphan nodes in the network
        dnodes: set, the duplicated nodes in network
        unodes: set, no defined nodes in the network
        dlinks: set, the duplicated links in network"""

        # ORPHAN NODES SEARCH
        onodes = set()
        for node in self.nodes:
            onodes.add(node.nodeid)

        for link in self.links:
            onodes.discard(link.start)
            onodes.discard(link.end)

        # DUPLICATE NODEID SEARCH
        dnodes = set()
        for i in range(len(self.nodes)-1):
            for j in range(i+1, len(self.nodes)):
                if self.nodes[i].nodeid == self.nodes[j].nodeid:
                    dnodes.add(self.nodes[j.nodeid])

        # UNDEFINED START AND END NODES
        unodes = set()
        for link in self.links:
            if not isinstance(self.get_nodeindex(link.start), int):
                unodes.add(link.start)
            if not isinstance(self.get_nodeindex(link.end), int):
                unodes.add(link.end)

        # DUPLICATED LINKID SEARCH
        dlinks = set()
        for i in range(len(self.links)-1):
            for j in range(i+1, len(self.links)):
                if self.links[i].linkid == self.links[j].linkid:
                    dlinks.add(self.links[j].linkid)

        return onodes, dnodes, unodes, dlinks

    def degree(self):
        """Calculate the node degrees."""
        # CALCULATE DEGREE
        for node in self.nodes:
            node.degree = 0
        for link in self.links:
            self.nodes[self.get_nodeindex(link.start)].degree += 1
            self.nodes[self.get_nodeindex(link.end)].degree += 1
