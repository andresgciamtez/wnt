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
    crs = root.find(xmlname('CoordinateSystem'))
    epsg_code = None
    wkt_crs = None
    if 'epsgCode' in crs.attrib:
        epsg_code = crs.attrib['epsgCode']
    else:
        wkt_crs = crs.attrib['ogcWktCode']
    networks = {}

    # READ NETWORK
    for pipenetwork in root.iter(xmlname('PipeNetwork')):
        net_type = pipenetwork.attrib['pipeNetType']
        if net_type == 'storm':

            #READ STRUCTS
            nodes = {}
            inverts = {}
            for struct in pipenetwork.iter(xmlname('Struct')):
                name = struct.attrib['name']
                desc = struct.attrib['desc']
                if desc != "Dummy Null Structure for LandXML purposes":
                    node = {}
                    sump = round(float(struct.attrib['elevSump']), 3)
                    node['elev_sump'] = sump
                    rim = round(float(struct.attrib['elevRim']), 3)
                    node['elev_rim'] = rim
                    node['depth'] = round(rim - sump, 3)

                    # CONNECTED PIPES
                    for child in list(struct):
                        if child.tag == xmlname('Center'):
                            y, x = map(float, child.text.split())
                            node['x'] = x
                            node['y'] = y
                        if child.tag == xmlname('Invert'):
                            pipe = child.attrib['refPipe']
                            invert = {}
                            elev = round(float(child.attrib['elev']), 3)
                            invert['elev'] = elev
                            offset = round(elev - node['elev_sump'], 3)
                            invert['offset'] = offset
                            depth = round(node['elev_rim'] - elev, 3)
                            invert['depth'] = depth
                            inverts[(pipe, name)] = invert
                    nodes[name] = node

            # READ PIPES
            links = {}
            for pipe in pipenetwork.iter(xmlname('Pipe')):
                name = pipe.attrib['name']
                start = pipe.attrib['refStart']
                end = pipe.attrib['refEnd']
                pipe_data = {'start': start,
                             'end': end,
                             'start_elev': inverts[(name, start)]['elev'],
                             'start_offset': inverts[(name, start)]['offset'],
                             'start_depth': inverts[(name, start)]['depth'],
                             'end_elev': inverts[(name, end)]['elev'],
                             'end_offset': inverts[(name, end)]['offset'],
                             'end_depth': inverts[(name, end)]['depth'],
                             'length': round(float(pipe.attrib['length']), 3),
                             'slope': round(float(pipe.attrib['slope']), 4)
                             }
                for child in list(pipe):
                    if child.tag == xmlname('CircPipe'):
                        pipe_data['sect_type'] = 'CircPipe'
                        pipe_data['section'] = child.attrib['diameter']
                    if child.tag == xmlname('RectPipe'):
                        pipe_data['sect_type'] = 'RectPipe'
                        sect = child.attrib['width'] + 'X'
                        pipe_data['section'] = sect + child.attrib['height']
                links[name] = pipe_data
        else:
            MSG = 'Pressurized networks not implemented yet!'
            raise NotImplementedError(MSG)

    # RETURN NETWORKS
        networks[pipenetwork.attrib['name']] = {'nodes': nodes,
                                                'links': links,
                                                'net_type': net_type
                                                }
    if epsg_code:
        return {'networks': networks, 'epsg_code': epsg_code}
    return {'networks': networks, 'wkt_crs': wkt_crs}
