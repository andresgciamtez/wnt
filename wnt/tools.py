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

from os.path import exists as fexits
import csv
from . import htxt

class Node:
    '''Node class'''
    def __init__(self, nodeid):
        self.nodeid = nodeid
        self._type = None
        self._x = None
        self._y = None
        self.elevation = None
        
    def set_geometry(self, coor):
        msg = 'Incorrect node geometry, it must be a (x, y) tuple'
        assert type(coor[0]) == type(coor[1]) == float , msg 
        self._x,self._y = coor[:]
        
    def get_geometry(self):
        msg = 'Not defined/error in node coordinates'
        assert type(self._x) == type(self._x) == float, msg
        return (self._x,self._y)
    
    def set_type(self, nodetype):
        msg = 'Incorrect node type, it must be: JUNCTION/RESERVOIR/TANK'
        assert nodetype in ('JUNCTION', 'RESERVOIR', 'TANK'), msg
        self._type = nodetype
    
    def get_type(self):
        return self._type
    
    def get_distance2d(self, point2):
        '''Return the 2d distance to point2 (x2,y2)'''
        msg = 'Incorrect point 2 geometry, it must be a (x, y) tuple'
        assert type(point2[0]) == type(point2[1]) == float , msg 
        return ((self._x-point2[0])**2+((self._y-point2[1])**2))**0.5
    
    def set_wkt(self, wkt):
        '''Set the geometry from a point in WKT format, "POINT (x y)"'''
        point = wkt.upper()
        for s in ['POINT', '(', ')', '"', '\n']:
            point = point.replace(s, '')
            
        point = point.strip().split()
        point = float(point[0]),float(point[1])
        msg = 'Incorrect WKT point format'
        assert type(point[0]) == type(point[1]) == float, msg
        self.set_geometry(point) 
    
    def get_wkt(self):
        '''Return the node geometry in WKT format, "POINT (x y)"'''
        msg = 'Not defined/error in node coordinates'
        assert type(self._x) == type(self._x) == float, msg
        return 'POINT ({} {})'.format(self._x, self._y)               

class Link:
    '''Link class'''
    def __init__(self, linkid, start, end):
        self.linkid = linkid
        self.start = start
        self.end = end
        self._linktype = None
        self._polyline = None
        self._length = None
        
    def set_geometry(self, polyline):
        msg = 'Incorrect geometry, it must be a tuple of tuples((x0,y0), ...'
        for vertex in polyline:
            assert type(float(vertex[0])) == type(float(vertex[1])) ==float,msg
        
        self._polyline = polyline
        
    def set_type(self, linktype):
        msg = 'Incorrect link type, it must be: PIPE/PUMP/VALVE'
        linktypes = ['PIPE', 'PUMP', 'PRV', 'PSV', 'PBV', 'FCV','TCV','GPV']
        assert linktype in linktypes, msg
        self._type = linktype
    
    def get_type(self):
        return self._type
        
    def get_startpoint(self):
        '''Return the initial point'''
        assert type(self._polyline) != type(None), 'Not defined geometry'
        return self._polyline[0]
    
    def get_endpoint(self):
        '''Return the final point'''
        assert type(self._polyline) != type(None), 'Not defined geometry'
        return self._polyline[-1]   
    
    def get_vertices(self):
        '''Return the middle vertices'''
        assert type(self._polyline) != type(None), 'Not defined geometry'
        return self._polyline[1:-1]
    
    def length2d(self):
        '''Return the 2D length'''
        pol = self._polyline
        assert type(pol) != type(None), 'Not defined geometry'
        length = 0.0
        for i in range(len(pol)-1):
            dx = pol[i][0]-pol[i+1][0]
            dy = pol[i][1]-pol[i+1][1]
            length += (dx**2+dy**2)**0.5
            
        return length
    
    def set_wkt(self, wkt):
        '''Set the geometry from a WKT format, "LineString (x0 y0, ...)"'''
        points = wkt.upper()
        #assert not ('MULTI' in wkt), 'Multi-geometry is not supported'
        
        for s in ['MULTI', 'LINESTRING', '(', ')', '"', '\n']:
            points = points.replace(s, '')
            
        points = points.strip().split(',')
        msg = 'Incorrect WKT LineString format'
        polyline = []
        for point in points:       
            x,y = point.split() 
            x,y = float(x),float(y)
            assert type(x) == type(x) == float, msg
            polyline.append((x,y))
        
        self.set_geometry(tuple(polyline))
    
    def get_wkt(self):
        '''Return the node geometry in WKT format. "LineString (x0 y0, ...)"'''        
        assert type(self._polyline) != type(None), 'Not defined geometry'
        tmp = 'LINESTRING (' 
        for point in self._polyline[0:-1]:
            tmp += str(point[0]) + ' ' + str(point[1]) + ',' 

        point = self._polyline[-1]
        return tmp + str(point[0]) + ' ' + str(point[1]) + ')'   

class Network:
    '''Main class. A network is represented by two lists: nodes and lines.
    
    Make the topology and geometry of a network from a file of lines in WKT 
    format.
    It contains functions for the conversion between GIS and epanet formats.
    '''
    
    def __init__(self):
        self.nodes = []
        self.links = []
        
    def get_nodeindex(self, nodeid):
        '''Return the index in nodes, None  if node not exits '''
        for index in range(len(self.nodes)):
            if self.nodes[index].nodeid == nodeid:
                return index
        
        return None # if node not exit
        
    def get_linkindex(self, linkid):
        '''Return the index in nodes, None  if node not exits '''
        for index in range(len(self.links)):
            if self.links[index].linkid == linkid:
                return index
                
        return None # if link not exit            
    
    def dist2p(self, point1, point2):
        '''Distance 2D between 2 points, (x1,y1) and (x2,y2)'''
        return ((point1[0]-point2[0])**2+((point1[1]-point2[1])**2))**0.5
    
    def nodes_to_geocsv(self, fn):
        '''Export nodes in geoCSV format'''
        with open(fn, encoding='utf-8-sig', mode='w') as csvfile:
            fields =['geometry', 'id', 'type', 'elevation']
            
            writer = csv.DictWriter(csvfile, fields)
            writer.writeheader()
            for node in self.nodes:
                nodeDic = {'geometry': node.get_wkt(),  \
                           'id': node.nodeid,           \
                           'type': node.get_type(),     \
                           'elevation': node.elevation  \
                           }
                writer.writerow(nodeDic)
        
    def links_to_geocsv(self, fn):
        '''Export links in geoCSV format'''
        with open(fn, encoding='utf-8-sig', mode='w') as csvfile:
            fields =['geometry','id','start','end','type', 'length']
            writer = csv.DictWriter(csvfile, fields)
            writer.writeheader()
            for link in self.links:
                nodeDic = {'geometry': link.get_wkt(),  \
                           'id': link.linkid,           \
                           'start': link.start,         \
                           'end': link.end,             \
                           'type': link.get_type(),     \
                           'length': link.length2d()  \
                           }
                writer.writerow(nodeDic)
    

    def from_lines(self, lines, t=0.0, nodeprefix='Node-', nodeinit=0, \
                   nodedelta=1, linkprefix='Link-', linkinit=0, linkdelta=1):
        '''Make a network (geometry and topology) from txt lines in WKT format
        
        Parameters
        ----------
        
        lines: list, containing txt lines geometry as WKT (LineString)
        t: float, nodes separated lesser than t are merged
        linkprefix: str, prefix of node id label
        linkinit: int, link initial numeration
        linkdelta: int, link increment numeration
        linkprefix: str, prefix of link id label
        linkinit: int, link initial numeration
        linkdelta: int, link increment numeration
        '''    
        # LOAD LINKS
        links = []
        linkcnt = 0

        for line in lines:
            if 'LINESTRING' in line.upper():
                linkid = linkprefix + str(linkinit + linkdelta*linkcnt)
                mylink = Link(linkid, linkcnt*2, linkcnt*2+1)
                mylink.set_type('PIPE')
                mylink.set_wkt(line)                                           
                links.append(mylink)
                linkcnt += 1
        
        # REDUCING OVERLAPPED POINTS
        usednodes = set()
        cnt = 0
        for i in range(len(links)):
            assert links[i].length2d() >= 2*t, 'Too short link'        
            if not(links[i].start in usednodes):
                links[i].start = cnt
                usednodes.add(cnt)
                cnt += 1
     
            if not(links[i].end in usednodes):
                links[i].end = cnt
                usednodes.add(cnt)
                cnt += 1
            
            point1 = links[i].get_startpoint()
            point2 = links[i].get_endpoint()
            # MERGE
            for j in range(i+1,len(links)):
                point3 = links[j].get_startpoint()
                point4 = links[j].get_endpoint()
                if self.dist2p(point3, point1) <= t:
                    links[j].start = links[i].start
    
                elif self.dist2p(point4, point1) <= t:
                    links[j].end = links[i].start
    
                if self.dist2p(point3, point2) <= t:
                    links[j].start = links[i].end
    
                elif self.dist2p(point4, point2) <= t:
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
        
        for key in avgcoor.keys():
            n = len(avgcoor[key])
            x,y = 0,0
            for coor in avgcoor[key]:
                x += coor[0]
                y += coor[1]
            avgcoor[key] = (x/n,y/n)   
    
        # CREATE NODES
        nodes = []    
        rename = {}
        for key in avgcoor.keys():
            nodeid = nodeprefix + str(nodeinit + nodedelta * key)
            rename[key] = nodeid
            mynode = Node(nodeid)
            mynode.set_geometry(avgcoor[key])
            mynode.elevation = 0.0
            nodes.append(mynode)
        
        # UPDATE LINKS
        for link in links:
            link.start = rename[link.start]
            link.end = rename[link.end]

        # UPDATE NETWORK
        self.nodes = nodes
        self.links = links        
    
    def from_csv(self, nodescsv, linkscsv):
        '''Import a network from geocsv data'
        
        Node data: id, geometry [, type, elevation]
        Link data: id, start, end, geometry [,type]
        
        Parameters
        ----------
        
        nodescsv: file name, input node file in geocsv format
        linkscsv: file name, input link file in geocsv format
        '''  
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
                newnode.set_wkt(row['geometry'])
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
                newlink.set_wkt(row['geometry'])
                if 'type' in reader.fieldnames:
                    tmp = ['PIPE','PUMP','PRV','PSV','PBV','FCV','TCV','GPV']
                    if row['type'] in tmp:
                        newlink.set_type(row['type'])
                    else:
                        newlink.set_type('PIPE')
               
                #  IT IS PENDING TO IMPLEMENT THE REST OF PARAMETERS !
            
                # ADD NEW LINK
                self.links.append(newlink)  
    
    def from_epanet(self, epanetfn):
        '''Make a network from a epanet file
        
        Node data: id, type, elevation and coordinates.
        Link data: id, type, start, end, type, vertices.
        
        IT IS PENDING TO IMPLEMENT THE REST OF PARAMETERS !
        
        Parameters
        ----------
        
         epanetfn: epanet file name (*.inp), input epanet model
        
        '''
        # READ EPANET FILE
        myht = htxt.Htxtf(epanetfn)
        mysections = myht.read()
        
        # INPUT JUNCTIONS # ID Elev Demand Pattern    
        for line in  mysections['JUNCTIONS']:
            tmp = myht.line_to_tuple(line)
            junction = Node(tmp[0])
            junction.set_type('JUNCTION')
            junction.elevation = tmp[1] 
            self.nodes.append(junction)
            
        # INPUT RESERVOIRS # ID Head Pattern      
        for line in  mysections['RESERVOIRS']:
            tmp = myht.line_to_tuple(line)
            reservoir = Node(tmp[0])
            reservoir.set_type('RESERVOIR')
            reservoir.elevation = tmp[1] 
            self.nodes.append(reservoir)

        # INPUT TANKS # ID Elevation InitLevel MinLevel MaxLevel Diameter MinVol VolCurve
        for line in  mysections['TANKS']:      
            tmp = myht.line_to_tuple(line)
            tank = Node(tmp[0])
            tank.set_type('TANK')
            tank.elevation = tmp[1]
            self.nodes.append(tank)
        
        # COORDINATES
        for line in mysections['COORDINATES']:
            nid,x,y = myht.line_to_tuple(line)
            index = self.get_nodeindex(nid)
            self.nodes[index].set_geometry((float(x),float(y)))         
        
        # INPUT PIPES # ID Node1 Node2 Length Diameter Roughness MinorLoss Status
        for line in  mysections['PIPES']:      
            tmp = myht.line_to_tuple(line)
            lid,n1,n2 = tmp[0:3]
            s = tmp[-1]
            pipe = Link(lid, n1, n2)
            if s == "CV":
                pipe.set_type('CVPIPE')
            else:
                pipe.set_type('PIPE')
                
            pipe._length = tmp[3]
            pipe.diameter = tmp[4]
            pipe.roughness = tmp[5]            
            self.links.append(pipe)
        
        # INPUT PUMPS #  # ID Node1 Node2 Parameters
        for line in  mysections['PUMPS']:
            tmp = myht.line_to_tuple(line)
            lid,n1,n2 = tmp[0:3]
            pump = Link(lid, n1, n2)
            pump.set_type('PUMP')          
            self.links.append(pump)
        
        # INPUT VALVES # ID Node1 Node2 Diameter Type Setting MinorLoss
        for line in  mysections['VALVES']:
            tmp = myht.line_to_tuple(line)
            lid,n1,n2 = tmp[0:3]
            t = tmp[4]
            valve = Link(lid,n1,n2)
            valve.set_type(t)
            self.links.append(valve)
        
        # VERTICES
        for link in self.links:
            tmp = [self.nodes[self.get_nodeindex(link.start)].get_geometry()]
            tmp.append(self.nodes[self.get_nodeindex(link.end)].get_geometry())
            link.set_geometry(tmp)
            
        for line in mysections['VERTICES']:
            nid,x,y = myht.line_to_tuple(line)
            index = self.get_linkindex(nid)
            poly = self.links[index]._polyline
            poly.insert(-1,(float(x),float(y)))
            
    def to_epanet(self, epafn, temfn='./template.inp', lengths=True):
        '''Export network to an epanet file'
        
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
        
        epafn: epanet file name (*.inp), output epanet model
        temfn: template epanet file name (*.inp)
        lengths: boolean, calculate pipe lengths '''
        
        # READ EPANET FILE TEMPLATE
        epanetf = htxt.Htxtf(temfn)
        sections = epanetf.read()
        
        # NODES/COORDINATES TO SECTION
        for node in self.nodes:
            nodetype = node.get_type()
            if (nodetype == 'JUNCTION'):
                if type(node.elevation) != type(None):
                    tmp = (node.nodeid,node.elevation,0.0)
                else:
                    tmp = (node.nodeid,0.0,0.0)
                sections['JUNCTIONS'].append(epanetf.tuple_to_line(tmp))
                
            elif nodetype == 'RESERVOIR':
                if type(node.elevation) != type(None):
                    tmp = (node.nodeid,node.elevation)
                else:
                    tmp = (node.nodeid,0.0)
                sections['RESERVOIRS'].append(epanetf.tuple_to_line(tmp))
            
            elif nodetype == 'TANK':
                if type(node.elevation) != type(None):
                    tmp = (node.nodeid,node.elevation,0.0,0.0,0.0,0.0,0.0)
                else:
                    tmp = (node.nodeid,0.0,0.0,0.0,0.0,0.0,0.0)
                sections['TANKS'].append(epanetf.tuple_to_line(tmp))

            line = epanetf.tuple_to_line((node.nodeid,node._x,node._y))
            sections['COORDINATES'].append(line)
        
        # LINKS/VERTICES TO SECTION 
        for link in self.links:
            linktype = link.get_type()
            # (id,start,end, ...
            tmp = (link.linkid,link.start,link.end)
            if (linktype in ['PIPE', 'CVPIPE']) or (type(linktype) == type(None)):
                # length,diameter,roughness,minorLoss, ...
                if lengths:
                    tmp = tmp + (link.length2d(),0.0,0.0,0.0)
                else:
                    tmp = tmp + (0.0,0.0,0.0,0.0)
                
                # status)
                if linktype == 'CVPIPE':
                    tmp = tmp + ('CV',)
                else:
                    tmp = tmp + ('Open',)
                    
                sections['PIPES'].append(epanetf.tuple_to_line(tmp))
            
            if linktype == 'CVPIPE':
               tmp = (link.linkid,link.start,link.end,0.0,0.0,0.0,0.0, \
                      'CV')
               sections['PIPES'].append(epanetf.tuple_to_line(tmp))
            
            elif linktype == 'PUMP':
                tmp= (link.linkid,link.start,link.end,'POWER')
                sections['PUMPS'].append(epanetf.tuple_to_line(tmp))
            
            elif linktype in ['PRV', 'PSV', 'PBV', 'FCV','TCV','GPV']:
                tmp = (link.linkid,link.start,link.end,linktype,0.0,0.0)
                sections['VALVES'].append(epanetf.tuple_to_line(tmp))
            
            vertices = link.get_vertices()
            if type(vertices) != type(None):
                for vertice in vertices:
                    tmp = (link.linkid,vertice[0],vertice[1])
                    sections['VERTICES'].append(epanetf.tuple_to_line(tmp))
        
        # RESIZE [BACKDROP]
        x1,y1,x2,y2 = 1e12,1e12,-1e12,-1e12
        for node in self.nodes:
            if node._x < x1:
                x1 = node._x
            elif node._x > x2:
                x2 = node._x
            if node._y < y1:
                y1 = node._y
            elif node._y > y2:
                y2 = node._y
        
        dx,dy = x2-x1,y2-y1
        x1,y1,x2,y2 = x1-0.1*dx,y1-0.1*dy ,x2+0.1*dx,y2+0.1*dy
                
        newsection = []
        for line in sections['BACKDROP']:
            # SERCH DIMENSIONS
            if 'DIMENSIONS' in line:
                newline = 'DIMENSIONS  {}  {}  {}  {}'.format(x1,y1,x2,y2)
            # BYPASS    
            else:
                newline = line
            
            newsection.append(newline)
        
        sections['BACKDROP'] = newsection
        
        # WRITE EPANET INP FILE
        outputf = open(epafn, 'w')
        outputf.write('; File generated automatically by nettools.py \n')
        for section in sections:
            outputf.write('[' + section + '] \n')
            for line in sections[section]:
                outputf.write(line + ' \n')
            outputf.write(' \n')
        
        outputf.write('[END] \n')
        outputf.close()
        
    def to_tgf(self, fn):
        '''Export network topology to Trivial Graph Format (TGF)'''
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
        '''Analyze the network graph. Return the number of orphan nodes'''
        # CALCULATE DEGREE
        for node in self.nodes:
            node._degree = 0
        
        for link in self.links:
            self.nodes[self.get_nodeindex(link.start)]._degree += 1
            self.nodes[self.get_nodeindex(link.end)]._degree += 1

        # RETURN ORPHAN NODE COUNT
        return sum([node._degree == 0 for node in self.nodes])
    
    def boundbox(self, line, tolerance=0.0):
        '''Return the rectangular boxbound of a line.'''
        assert type(line) == list, 'Line is not a list'
        
        x1,y1 = x2,y2 = line[0] 
        
        for point in line[1:]:
            x = point[0]
            y = point[1]
            
            x1 = min(x1,x)
            y1 = min(y1,y)
            x2 = max(x2,x)
            y2 = max(y2,y)

        x1 -= tolerance
        y1 -= tolerance
        x2 += tolerance
        y2 += tolerance
        
        return (x1,y1,x2,y2)
    
    def in_boundbox(self, point, boundbox):
        '''Return True if the point is inside boxbound'''
        x,y = point
        x1,y1,x2,y2 = boundbox
        
        if x < x1 or x > x2 or y < y1 or y > y2:
            return False
        else:
            return True 
    
    
    def split_line(self, line, point, tolerance=0.0):
        '''Split a (poly)line (2D) at point if point is over it.
        Line is a list of tuples containing vertex (x,y)'''
        # CHECK TYPES
        assert type(line) == list, 'Line is not a list'
        assert type(point) == tuple, 'Point is not a tuple'
               
        # SPLIT PLINE
        # SEGMENT LOOP
        n = len(line)-1
        for i in range(n):
            xa,ya = line[i][0:2]
            xb,yb = line[i+1][0:2]
            ab = self.dist2p((xa,ya),(xb,yb))
            
            # IGNORE TOO SHORT SEGMENT
            if ab > tolerance:
                xp,yp = point[0:2]                
                pc = abs((xb-xa)*(yp-ya)-(yb-ya)*(xp-xa))/ab
                
                # DETECTED PROXIMITY
                if pc <= tolerance:    
                    
                    # IGNORE INTERSECTION AT POLYLINE START POINT
                    ap = self.dist2p((xa,ya),(xp,yp))
                    if i == 0 and ap <= tolerance:    
                        return False, None
                    
                    # IGNORE INTERSECTION AT POLYLINE END POINT
                    bp = self.dist2p((xb,yb),(xp,yp))
                    if i == n and bp <= tolerance:
                        return False, None
                    
                    # CHECK INNER INTERSECTION
                    cs = ((xp-xa)*(xb-xa)+(yp-ya)*(yb-ya))/(ap*ab)
                    xc = xa + cs*ap/ab*(xb-xa)
                    yc = ya + cs*ap/ab*(yb-ya)
                    ac = self.dist2p((xa,ya),(xc,yc))
                    bc = self.dist2p((xb,yb),(xc,yc))
                    
                    # SPLIT
                    if ac + bc <= ab:   
                        linea = line[0:i+1].copy()
                        linea.append((xc,yc))
                        lineb = line[i+1:].copy()
                        lineb.insert(0,(xc,yc))
                        return True,tuple([linea,lineb])
                
        return False, None
    
    def split_lines(self, lines, points, tolerance=0.0):
        '''Divide (poly)lines (2D) at points if point is over it.
        lines is a list of polylines. See divide_line().
        points is a list of tuples (x,y).'''
        assert type(lines) == list, 'polyline is not a list' 
        assert type(points) == list, 'points is not a list'        

        result = lines.copy()
        
        # POINTS LOOP
        for point in points:
            
            # LINES LOOP
            for index in range(len(result)):
                line = result[index]
                print(type(line))
            
                # IGNORE POINTS OUT OF BOUND BOX
                if self.in_boundbox(point,self.boundbox(line, tolerance)):
                    
                    # SPLIT
                    changed,splited = self.split_line(line,point,tolerance)
                        
                    # CHANGE OLD LINE AND ADD NEW    
                    if changed:
                        result[index] = splited[0]  # FIRST PART
                        result.append(splited[1])   # SECOND PART
                        break

        return result
