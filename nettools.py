# -*- coding: utf-8 -*-
"""NETTOOLS IMPORT/EXPORT WATER NETWORK FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
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
    
    def get_wkt(self):
        '''Return the node geometry in WKT format, "POINT (x y)"'''
        msg = 'Not defined/error in node coordinates'
        assert type(self._x) == type(self._x) == float, msg
        return 'POINT ({} {})'.format(self._x, self._y)
    
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
                

class Link:
    '''Link class'''
    def __init__(self, linkid, start, end):
        self.linkid = linkid
        self.start = start
        self.end = end
        self._linktype = None
        self._polyline = None
        
    def set_geometry(self, polyline):
        msg = 'Incorrect geometry, it must be a tuple of tuples((x0,y0), ...'
        for coor in polyline:
            assert type(float(coor[0])) == type(float(coor[1])) == float, msg
        
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
    
    def get_length(self):
        '''Return the 2D length'''
        pol = self._polyline
        assert type(pol) != type(None), 'Not defined geometry'
        length = 0.0
        for i in range(len(pol)-1):
            dx = pol[i][0]-pol[i+1][0]
            dy = pol[i][1]-pol[i+1][1]
            length += (dx**2+dy**2)**0.5
            
        return length
    
    def get_wkt(self):
        '''Return the node geometry in WKT format. "LineString (x0 y0, ...)"'''        
        assert type(self._polyline) != type(None), 'Not defined geometry'
        tmp = 'LINESTRING (' 
        for point in self._polyline[0:-1]:
            tmp += str(point[0]) + ' ' + str(point[1]) + ',' 

        point = self._polyline[-1]
        return tmp + str(point[0]) + ' ' + str(point[1]) + ')'
    
    def set_wkt(self, wkt):
        '''Set the geometry from a WKT format, "LineString (x0 y0, ...)"'''
        points = wkt.upper()
        assert not ('MULTI' in wkt), 'Multi-geometry is not supported'
        
        for s in ['LINESTRING', '(', ')', '"', '\n']:
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
   

class Network:
    '''Main class. A network is represented by two lists: nodes and lines.
    
    It allows generating the topology and geometry of a network from a
    file of lines in WKT format. It contains several functions for the 
    conversion between geocsv and epanet formats.
    It allows the update of epanet files from GIS data.'''
    
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
                           'length': link.get_length()  \
                           }
                writer.writerow(nodeDic)
    

    def network_from_lines(self, fn, t=0.1, prene='Node-', initne=0, \
                           incrne=1, prelk='Link-', initlk=0, incrlk=1):
        '''Make a network geometry and topology from lines
        
        Node data: id, x and y.
        Link data: id, start, end and vertices.
        
        Parameters
        ----------
        
        fn: geocsv file name, containing lines geometry as WKT (linestring)
        t: float, nodes separated lesser than t are merged
        prelk: str, prefix of node id label
        initlk: int, link initial numeration
        incrlk: int, link increment numeration
        prelk: str, prefix of link id label
        initlk: int, link initial numeration
        incrlk: int, link increment numeration
        
        Return
        ------
        A NetTools object
        '''    
        # LOAD LINKS
        links = []
        linkcnt = 0
        with open(fn, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if 'LINESTRING' in line.upper():
                    linkid = prelk + str(initlk + incrlk*linkcnt)
                    mylink = Link(linkid, linkcnt*2, linkcnt*2+1)
                    mylink.set_type('PIPE')
                    mylink.set_wkt(line)                                              
                    links.append(mylink)
                    linkcnt += 1
        
        # REDUCING OVERLAPPED POINTS
        usednodes = set()
        cnt = 0
        for i in range(len(links)):
            assert links[i].get_length() >= 2*t, 'Too short link'        
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
            nodeid = prene + str(initne + incrne * key)
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
    
    def network_from_geocsv(self, nodescsv, linkscsv):
        '''Import a network from GIS data'
        
        Node data: id, geometry [, type, elevation]
        Link data: id, start, end, geometry [,type]
        
        Parameters
        ----------
        
        nodescsv: file name, input node file in geocsv format
        linkscsv: file name, input link file in geocsv format'''  
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
                    newnode.set_type(row['elevation'])
                    
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
    
    def network_from_epanet(self, epanetfn):
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
            junction = Node(tmp[0], nodetype='JUNCTION')
            self.nodes.append(junction)
            
        # INPUT RESERVOIRS # ID Head Pattern      
        for line in  mysections['RESERVOIRS']:
            tmp = myht.line_to_tuple(line)
            reservoir = Node(tmp[0], nodetype='RESERVOIR')
            self.nodes.append(reservoir)

        # INPUT TANKS # ID Elevation InitLevel MinLevel MaxLevel Diameter MinVol VolCurve
        for line in  mysections['TANKS']:      
            tmp = myht.line_to_tuple(line)
            tank = Node(tmp[0], nodetype='TANK')
            self.nodes.append(tank)
        
        # COORDINATES
        for line in mysections['COORDINATES']:
            nid,x,y = myht.line_to_tuple(line)
            index = self.get_nodeindex(nid)
            self.nodes[index].x,self.nodes[index].y = float(x),float(y)         
        
        # INPUT PIPES # ID Node1 Node2 Length Diameter Roughness MinorLoss Status
        for line in  mysections['PIPES']:      
            tmp = myht.line_to_tuple(line)
            lid,n1,n2 = tmp[0:3]
            s = tmp[7]
            pipe = Link(lid, n1, n2)
            if s == "CV":
                pipe.linktype = 'CVPIPE'
            else:
                pipe.linktype = 'PIPE'
                
            self.links.append(pipe)
        
        # INPUT PUMPS #  # ID Node1 Node2 Parameters
        for line in  mysections['PUMPS']:
            tmp = myht.line_to_tuple(line)
            lid,n1,n2 = tmp[0:3]
            pump = Link(lid, n1, n2, linktype='PUMP' )          
            self.links.append(pump)
        
        # INPUT VALVES # ID Node1 Node2 Diameter Type Setting MinorLoss
        for line in  mysections['VALVES']:
            tmp = myht.line_to_tuple(line)
            lid,n1,n2 = tmp[0:3]
            t = tmp[4]
            valve = Link(lid,n1,n2)
            valve.linktype = t
            self.links.append(valve)
        
        # VERTICES
        for line in mysections['VERTICES']:
            nid,x,y = myht.line_to_tuple(line)
            index = self.get_linkindex(nid)
            if type(self.links[index].vertices) == type(None):
                self.links[index].vertices = [(float(x),float(y))]
            else:
               self.links[index].vertices.append((float(x),float(y)))                          
    
    def network_to_epanet(self, epanetfn, lengths=True):
        '''Export network to an epanet file'
        
        Data exported:
            [JUNTIONS]
            id / default parameters
            [RESERVOIRS]
            id / default parameters
            [TANKS]
            id / default parameters
            [PIPES]
            id start end / default parameters
            [PUMPS]
            id start end / default parameters
            [VALVES]
            id start end / default parameters
            [COORDINATES]
            id x y
            [VERTICES]
            id x y
        
        Parameters
        ----------
        
        epanetfn: epanet file name (*.inp), output epanet model
        lengths: boolean, calculate pipe lengths '''

        # CHECK IF TEMPLATE EXISTS
        templatefn = './template.inp'
        assert fexits(templatefn), 'Template file cannot be found'
        
        # READ EPANET FILE TEMPLATE
        epanetf = ht.Htxtf(templatefn)
        sections = epanetf.read()
        
        # NODES/COORDINATES TO SECTION
        for node in self.nodes:
            nodetype = node.get_type()
            if (nodetype == 'JUNCTION') or (type(nodetype) == type(None)):
                tmp = (node.nodeid,0.0,0.0)
                sections['JUNCTIONS'].append(epanetf.tuple_to_line(tmp))
                
            elif nodetype == 'RESERVOIR':
                tmp = (node.nodeid,0.0)
                sections['RESERVOIRS'].append(epanetf.tuple_to_line(tmp))
            
            elif nodetype == 'TANK':
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
                    tmp = tmp + (link.get_length(),)
                else:
                    tmp = tmp + (0.0,)
                
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
                tmp = (link.linkid,link.start,link.end,link.linktype,0.0,0.0)
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
        outputf = open(epanetfn, 'w')
        outputf.write('; File generated automatically by ppntools.py \n')
        for section in sections:
            outputf.write('[' + section + '] \n')
            for line in sections[section]:
                outputf.write(line + ' \n')
            outputf.write(' \n')
        
        outputf.write('[END] \n')
        outputf.close()



#*#*#*#*#*#*#
#   TEST    #
#*#*#*#*#*#*#
#mynode = Node('N-34')
#print('1:', type(mynode), mynode.nodeid)
##print(mynode.get_wkt())
#mynode.set_geometry((25.3,25.3))
###mynode.set_geometry(25.3,25.3)
#print('2:', mynode.get_geometry())
##mynode.set_geometry('de')
#print('3:', mynode.get_type())
#mynode.set_type('JUNCTION')
##mynode.set_type(25.3)
##mynode.set_type('APPLE')
#print('4:', mynode.get_type())
##print(mynode.get_distance(45.3,44.5))
##print(mynode.get_distance(25.3))
#print('5:', mynode.get_distance((45.3,44.5)))
#print('6:', mynode.get_wkt())
##mynode.set_wkt('PO 23.5 456.3')
#mynode.set_wkt('Point (23.5 456.3)')
#print('7:', mynode.get_wkt())
#mylink = Link('L-26','N-23','N-45')
#print('10:', type(mylink), mylink.linkid, mylink.start, mylink.end)
##mylink.set_geometry(4,6)
##mylink.set_geometry()
#tmp = ((34.5,67.34),(125.36,80.36),(235.68,70.68),(400.21,50.36),(425.6,55.36))
#mylink.set_geometry(tmp)
#print('11:', mylink._polyline)
#print('12:', mylink.get_startvertex(), mylink.get_endvertex())
#print('13:', mylink.get_vertices())
#print('14:', mylink.get_length())
##mylink.set_type()
##mylink.set_type('HG')
#mylink.set_type('PIPE')
#print('15:', mylink.get_type())
#print('16:', mylink.get_wkt())
##mylink.set_wkt('LINesTRI (25.36 125, 236.25 124 , 256.2 2548, 1.0 2.0)')
#mylink.set_wkt('LINesTRING (25.36 125, 236.25 124 , 256.2 2548, 1.0 2.0)')
#print('17:', mylink._polyline)

## EXAMPLE 1
#geocsvfn = './examples/1_example_lines.csv'
#mynet = Network()        
#mynet.network_from_lines(geocsvfn, t=5.0, prene='N-', prelk='L-')
#
#print("ID    type    x    y")
#for node in mynet.nodes:
#    print(node.nodeid, node.get_type(), node._x, node._y)
#
#print("ID    start    end    type    vertices")
#for link in mynet.links:
#    print(link.linkid,link.start,link.end,link.get_type(),link.get_length())
#
#nodescsv = './examples/1_example_nodes.csv'
#linkscsv = './examples/1_example_pipes.csv'      
#mynet.nodes_to_geocsv(nodescsv)
#mynet.links_to_geocsv(linkscsv)
#mynet.network_to_epanet('./examples/1_example.inp')

## EXAMPLE 2
#geocsvfn = './examples/2_example_lines.csv'
#mynet = Network()        
#mynet.network_from_lines(geocsvfn, t=0.1, prene='N-', initne=1000, incrne = 10,
#                         prelk='L-', initlk= 1000, incrlk = 10)
#
#mynet.network_to_epanet('./examples/2_example.inp')

