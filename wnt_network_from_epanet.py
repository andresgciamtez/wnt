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
from qgis.core import (QgsProcessingAlgorithm,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterCrs,
                       QgsGeometry,
                       QgsWkbTypes
                      )
from . import utils_core as tools

class NetworkFromEpanetAlgorithm(QgsProcessingAlgorithm):
    """
    Built a network from an epanet file.
    """

    # DEFINE CONSTANTS

    INPUT = 'INPUT'
    NODE_OUTPUT = 'NODE_OUTPUT'
    LINK_OUTPUT = 'LINK_OUTPUT'
    CRS = 'CRS'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        createInstance must return a new copy of algorithm.
        """
        return NetworkFromEpanetAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'network_from_epanet'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Network from epanet file')

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
        return self.tr('''Import an epanet inp file generating a network.
        The epanet data imported is:
        Nodes: *id *type (JUNCTIONS/RESERVOIRS/TANK) *elevation
        Links: *id *start *end *type (PIPE/CVPIPE/PUMP/PRV/PSV/PBV/FCV/TCV/GPV
        *length (if type is PIPE or CVPIPE) *diameter *roughness
        
        ===
        
        Importa un archivo epanet inp y genera una red.
        Los datos importados de epanet son:
        Nodes: *id *type (JUNCTIONS/RESERVOIRS/TANK) *elevation
        Links: *id *start *end *type (PIPE/CVPIPE/PUMP/PRV/PSV/PBV/FCV/TCV/GPV
        *length (if type is PIPE or CVPIPE) *diameter *roughness
        ''')

    def initAlgorithm(self, config=None):
        """
         Define the inputs and outputs of the algorithm.
        """

        # ADD INPUT FILE AND CRS SELECTOR
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Epanet file'),
                extension='inp'
                )
            )
        self.addParameter(
            QgsProcessingParameterCrs(
                self.CRS,
                self.tr('Coordinate reference system (CRS)')
                )
            )
        # ADD NODE AND LINK SINKS
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODE_OUTPUT,
                self.tr('Epanet nodes')
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINK_OUTPUT,
                self.tr('Epanet links'),
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        epanetf = self.parameterAsFile(parameters, self.INPUT, context)
        crs = self.parameterAsCrs(parameters, self.CRS, context)

        # SHOW INFO
        feedback.pushInfo('='*40)
        feedback.pushInfo('CRS is {}'.format(crs.authid()))

        # READ NETWORK
        network = tools.WntNetwork()
        network.from_epanet(epanetf)
        nodes = network.nodes()
        links = network.links()

        # GENERATE NODES LAYER
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("elevation", QVariant.Double))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.NODE_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point,
            crs
            )

        # ADD NODES
        ncnt = 0
        ntot = len(nodes)
        for node in nodes:
            #add feature to sink
            ncnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(node.to_wkt()))
            f.setAttributes([node.name(), node.get_type(), node.get_elevation()])

            # ADD NODE
            node_sink.addFeature(f)

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(50*ncnt/ntot) # Update the progress bar

        # GENERATE LINKS LAYER
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("start", QVariant.String))
        newfields.append(QgsField("end", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("length", QVariant.Double))
        newfields.append(QgsField("diameter", QVariant.Double))
        newfields.append(QgsField("roughness", QVariant.Double))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.LINK_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs
            )

        # ADD LINKS
        lcnt = 0
        ltot = len(links)
        for link in links:
            lcnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(link.to_wkt()))
            if link.get_type() in ['PIPE', 'CVPIPE']:
                f.setAttributes([link.name(),
                                link.start(),
                                link.end(),
                                link.get_type(),
                                link.epanet['length'],
                                link.epanet['diameter'],
                                link.epanet['roughness']]
                                )
            else:
                f.setAttributes(
                    [link.name(),
                     link.start(),
                     link.end(),
                     link.get_type(),
                     None,
                     None,
                     None]
                    )

            # ADD LINK
            link_sink.addFeature(f)

            # SHOW PROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/ltot) # Update the progress bar

        # SHOW INFO
        msg = 'Epanet model Loaded successfully.'
        feedback.pushInfo(msg)
        msg = 'Added: {} nodes.'.format(ncnt)
        feedback.pushInfo(msg)
        msg = 'Added: {} links.'.format(lcnt)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id, self.LINK_OUTPUT: link_id}
