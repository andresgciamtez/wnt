# -*- coding: utf-8 -*-

"""
Import pipe network stored in LandXML-1.2 format
Andrés García Martínez (ppnoptimizer@gmail.com)
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
__date__ = '2019-10-04'
__copyright__ = '(C) 2019 by Andrés García Martínez'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

import xml.etree.ElementTree as ET


def network_from_xml(xmlfn):
    '''Import network from a LandXLM file.'''
    def xmlname(name):
        prefix = '{http://www.landxml.org/schema/LandXML-1.2}'
        return prefix + name

    tree = ET.parse(xmlfn)
    root = tree.getroot()
    cs = root.find(xmlname('CoordinateSystem'))
    epsg = cs.attrib['epsgCode']
    networks = {}

    # READ NETWORK
    for pipenetwork in root.iter(xmlname('PipeNetwork')):
        net_type = pipenetwork.attrib['pipeNetType']

        #READ STRUCTS
        nodes = {}
        pipe_elevations = {}
        for struct in pipenetwork.iter(xmlname('Struct')):
            name = struct.attrib['name']
            if 'elevSump' in struct.attrib:
                elev = float(struct.attrib['elevSump'])
            else:
                elev = 0
            for child in list(struct):
                if child.tag == xmlname('Center'):
                    y, x = map(float, child.text.split())
                if child.tag == xmlname('Invert'):
                    refpipe = child.attrib['refPipe']
                    pelevation = float(child.attrib['elev'])
                    poffset = pelevation - elev
                    zdata = {'elev': pelevation, 'offset': poffset}
                    if refpipe not in pipe_elevations:
                        pipe_elevations[refpipe] = {}
                    pipe_elevations[refpipe] = {name: zdata}
            nodes[name] = {'x': x,
                           'y': y,
                           'elev': elev
                           }

        # READ PIPES
        links = {}
        for pipe in pipenetwork.iter(xmlname('Pipe')):
            name = pipe.attrib['name']
            start = pipe.attrib['refStart']
            end = pipe.attrib['refEnd']
            length = pipe.attrib['length']
            slope = pipe.attrib['slope']
            for child in list(pipe):
                if child.tag == xmlname('CircPipe'):
                    diameter = child.attrib['diameter']
                    material = child.attrib['material']

            links[name] = {'start': start,
                           'end': end,
                           'length': length,
                           'slope': slope,
                           'diameter': diameter,
                           'material': material
                           }

        # RETURN NETWORKS
        networks[pipenetwork.attrib['name']] = {'nodes': nodes,
                                                'links': links,
                                                'net_type': net_type
                                                }
    return {'networks': networks, 'epsg': epsg}
