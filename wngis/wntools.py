# -*- coding: utf-8 -*-
"""
WNTOOLS. WATER NETWORK MODELLING UTILITIES
IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
2019 Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from os.path import exists as fexits
import csv
import htxt as ht

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
    
    def get_distance(self, point2):
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
        
    def get_startvertex(self):
        '''Return the initial vertex'''
        assert type(self._polyline) != type(None), 'Not defined geometry'
        return self._polyline[0]
    
    def get_endvertex(self):
        '''Return the final vertex'''
        assert type(self._polyline) != type(None), 'Not defined geometry'
        return self._polyline[-1]   
    
    def get_vertices(self):
        '''Return the middle vertices'''
        assert type(self._polyline) != type(None), 'Not defined geometry'
        return self._polyline[1:-1]
    
    def get_length2d(self):
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
                           'length': link.get_length2d()  \
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
            assert links[i].get_length2d() >= 2*t, 'Too short link'        
            if not(links[i].start in usednodes):
                links[i].start = cnt
                usednodes.add(cnt)
                cnt += 1
     
            if not(links[i].end in usednodes):
                links[i].end = cnt
                usednodes.add(cnt)
                cnt += 1
            
            point1 = links[i].get_startvertex()
            point2 = links[i].get_endvertex()
            # MERGE
            for j in range(i+1,len(links)):
                point3 = links[j].get_startvertex()
                point4 = links[j].get_endvertex()
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
                avgcoor[link.start].append(link.get_startvertex())
            else:
                avgcoor[link.start] = [link.get_startvertex()]
            
            if link.end in avgcoor:
                avgcoor[link.end].append(link.get_endvertex())
            else:
                avgcoor[link.end] = [link.get_endvertex()]
        
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
        myht = ht.Htxtf(epanetfn)
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
        epanetf = ht.Htxtf(temfn)
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
                    tmp = tmp + (link.get_length2d(),0.0,0.0,0.0)
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
    
    def graph_degree(self):
        '''Get node degrees'''
        for node in self.nodes:
            node._degree = 0
        
        for link in self.links:
            self.nodes[self.get_nodeindex(link.start)]._degree += 1
            self.nodes[self.get_nodeindex(link.end)]._degree += 1
    
    def split_polyline(self, polyline, point, tolerance=0.0):
        '''Split a polyline (2D) at point if point is over the polyline.
        Polyline is a list/tuple of tuples containing vertex (x,y)'''
        if type(polyline) == tuple:
            poly = list(polyline)
        elif type(polyline) == list:
            poly = polyline
        else:
            raise TypeError('polyline is not a list/tuple')
        assert type(point) == tuple, 'point is not a tuple'
               
        for i in range(len(poly)-1):
            startp = poly[i]
            endp = polyline[i+1]
            a = self.dist2p(startp,point)
            b = self.dist2p(point, endp)
            c = self.dist2p(startp,endp)
            
            if a + b < c + tolerance:
                # DIVISION POINT IS NOT START/END POINT
                d1 = self.dist2p(point,poly[0])
                d2 = self.dist2p(point,poly[-1])
                xa,ya = startp[:]
                xb,yb = endp[:]
                xp,yp = point[:]
                d3 = abs((xb-xa)*(yp-ya)-(yb-ya)*(xp-xa))/c
                if  d1 > tolerance and d2 > tolerance and d3 < tolerance:
                    # DIVIDE    
                    cs = ((xp-xa)*(xb-xa)+(yp-ya)*(yb-ya))/(a*c)
                    x = startp[0] + cs*a/c*(endp[0]-startp[0])
                    y = startp[1] + cs*a/c*(endp[1]-startp[1])
                    polya = poly[0:i+1].copy()
                    polya.append((x,y))
                    polyb = poly[i+1:].copy()
                    polyb.insert(0,(x,y))
                    return True,tuple([polya,polyb])
                
        return False,()

    
    def split_polylines(self, polylines, points, tolerance=0.0):
        '''Divide polylines (2D) at points if point is over the polyline.
        polylines is a list of polylines. See divide_polyline().
        points is a list of tuples (x,y).'''
        assert type(polylines) == list, 'polyline is not a list' 
        assert type(points) == list, 'points is not a list'
        
        oldpolys = polylines.copy()
        for point in points:
            newpolys = []
            for poly in oldpolys:
                result,divided = self.split_polyline(poly,point,tolerance)
                if result:
                    newpolys.append(divided[0]) # FIRST PART
                    newpolys.append(divided[1]) # SECOND PART
                else:
                    newpolys.append(poly)
                
            oldpolys = newpolys.copy()
            
        return oldpolys
