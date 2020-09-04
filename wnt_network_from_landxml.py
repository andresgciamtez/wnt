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

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsCoordinateReferenceSystem,
                       QgsProcessingAlgorithm,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsLineString,
                       QgsPoint,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsGeometry,
                       QgsWkbTypes
                      )
from . import utils_landxml as landxml

class NetworkFromLandXMLAlgorithm(QgsProcessingAlgorithm):
    """
    Built a network from an epanet file.
    """

    # DEFINE CONSTANTS

    INPUT = 'INPUT'
    NODE_OUTPUT = 'NODE_OUTPUT'
    LINK_OUTPUT = 'LINK_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        createInstance must return a new copy of algorithm.
        """
        return NetworkFromLandXMLAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'network_from_landxml'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Network from LandXML file')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Import')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'import'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''Import pipe networks from LandXML v1.2 format.
        
        http://www.landxml.org/
        ===
        Importa redes de tuberías desde el formato LandXML v1.2.
        
        http://www.landxml.org/
        ''')

    def initAlgorithm(self, config=None):
        """
         Define the inputs and outputs of the algorithm.
        """

        # ADD INPUT FILE AND CRS SELECTOR
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('LandXML file'),
                extension='xml'
                )
            )

        # ADD NODE AND LINK SINKS
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODE_OUTPUT,
                self.tr('Nodes')
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINK_OUTPUT,
                self.tr('Links'),
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # READ NETWORK
        landxmlfn = self.parameterAsFile(parameters, self.INPUT, context)
        net = landxml.network_from_xml(landxmlfn)
        networks = net['networks']
        crs = QgsCoordinateReferenceSystem('EPSG:' + net['epsg'])

        # SHOW INFO
        feedback.pushInfo('='*40)
        feedback.pushInfo('CRS is {}'.format(crs.authid()))

        # GENERATE SINK LAYER
        newfields = QgsFields()
        newfields.append(QgsField("network", QVariant.String))
        newfields.append(QgsField("network_type", QVariant.String))
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("elev", QVariant.Double))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.NODE_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point,
            crs
            )

        newfields = QgsFields()
        newfields.append(QgsField("network", QVariant.String))
        newfields.append(QgsField("network_type", QVariant.String))
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("start", QVariant.String))
        newfields.append(QgsField("end", QVariant.String))
        newfields.append(QgsField("length", QVariant.Double))
        newfields.append(QgsField("diameter", QVariant.Double))
        newfields.append(QgsField("material", QVariant.String))
        newfields.append(QgsField("slope", QVariant.Double))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.LINK_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs
            )

        netcnt = nodcnt = lnkcnt = 0
        # ADD NETWORK
        for netname, network in networks.items():
            netcnt += 1
            net_type = network['net_type']
            # ADD NODES
            for nodename, node in network['nodes'].items():
                nodcnt += 1
                f = QgsFeature()
                point = QgsPoint(node['x'], node['y'])
                f.setGeometry(point)
                f.setAttributes([netname,
                                 net_type,
                                 nodename,
                                 node['elev']
                                 ])
                node_sink.addFeature(f)

            # ADD LINKS
            for linkname, link in network['links'].items():
                lnkcnt += 1
                g = QgsFeature()
                x = network['nodes'][link['start']]['x']
                y = network['nodes'][link['start']]['y']
                spoint = QgsPoint(x, y)
                x = network['nodes'][link['end']]['x']
                y = network['nodes'][link['end']]['y']
                epoint = QgsPoint(x, y)
                g.setGeometry(QgsGeometry(QgsLineString([spoint, epoint])))
                g.setAttributes([netname,
                                 net_type,
                                 linkname,
                                 link['start'],
                                 link['end'],
                                 link['length'],
                                 link['diameter'],
                                 link['material'],
                                 link['slope'],
                                 ])
                link_sink.addFeature(g)

        # SHOW PROGRESS
        feedback.setProgress(100) # Update the progress bar

        # SHOW INFO
        msg = 'LandXML Loaded successfully.'
        feedback.pushInfo(msg)
        msg = 'Added: {} networks.'.format(netcnt)
        feedback.pushInfo(msg)
        msg = 'Added: {} nodes.'.format(nodcnt)
        feedback.pushInfo(msg)
        msg = 'Added: {} links.'.format(lnkcnt)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id, self.LINK_OUTPUT: link_id}
