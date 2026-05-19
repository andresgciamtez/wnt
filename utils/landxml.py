"""LandXML pipe network parser."""

import xml.etree.ElementTree as ET

NS = '{http://www.landxml.org/schema/LandXML-1.2}'


def xmlname(name):
    return NS + name


def network_from_xml(xmlfn):
    '''Import network from a LandXML file.'''
    tree = ET.parse(xmlfn)
    root = tree.getroot()
    crs = root.find(xmlname('CoordinateSystem'))
    epsg_code = None
    wkt_crs = None
    if crs is not None:
        if 'epsgCode' in crs.attrib:
            epsg_code = crs.attrib['epsgCode']
        elif 'ogcWktCode' in crs.attrib:
            wkt_crs = crs.attrib['ogcWktCode']
    networks = {}

    # READ NETWORK
    for pipenetwork in root.iter(xmlname('PipeNetwork')):
        net_type = pipenetwork.attrib['pipeNetType']
        if net_type == 'storm':

            # READ STRUCTS
            nodes = {}
            inverts = {}
            for struct in pipenetwork.iter(xmlname('Struct')):
                name = struct.attrib['name']
                desc = struct.attrib.get('desc', '')
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
                start_invert = inverts.get((name, start))
                end_invert = inverts.get((name, end))
                if not start_invert or not end_invert:
                    continue
                pipe_data = {'start': start,
                             'end': end,
                             'start_elev': start_invert['elev'],
                             'start_offset': start_invert['offset'],
                             'start_depth': start_invert['depth'],
                             'end_elev': end_invert['elev'],
                             'end_offset': end_invert['offset'],
                             'end_depth': end_invert['depth'],
                             'length': round(float(pipe.attrib['length']), 3),
                             'slope': round(float(pipe.attrib.get('slope', 0)), 4),
                             'sect_type': None,
                             'section': None,
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
    if wkt_crs:
        return {'networks': networks, 'wkt_crs': wkt_crs}
    return {'networks': networks}

