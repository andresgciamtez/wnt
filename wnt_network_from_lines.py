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
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterString,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource
                      )
from . import tools

class NetworkFromLinesAlgorithm(QgsProcessingAlgorithm):
    """
    Built a network from lines.
    """

    # DEFINE CONSTANTS
    INPUT = 'INPUT'
    TOLERANCE = 'TOLERANCE'
    NODE_PREFIX = 'NODE_PREFIX'
    NODE_INIT = 'NODE_INIT'
    NODE_DELTA = 'NODE_DELTA'
    LINK_PREFIX = 'LINK_PREFIX'
    LINK_INIT = 'LINK_INIT'
    LINK_DELTA = 'LINK_DELTA'
    NODE_OUTPUT = 'NODE_OUTPUT'
    LINK_OUTPUT = 'LINK_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return NetworkFromLinesAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'network_from_lines'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Network from lines')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Build')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'build'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''Generate an epanet network from lines.
        The generated network consists of two layers: nodes and links.
        Line ends not separated more than tolerance are merged into a node.
        - The node layer will contain the fields:
        * id * type [1] * elevation ('type' not set)
        - The line layer will contain the fields:
        * id * start * end * type [2] * length ('Type' is set to PIPE, and the 
        length is calculated from the geometry of the input layer.)
        
        Limitations:
        - MultiGeometry is not supported
        - The Z coordinate is ignored
        
        Notes:
          [1] JUNCTION / RESERVOIR / TANK
          [2] PIPE / CVPIPE / PUMP / PRV / PSV / PBV / FCV / TCV / GPV
        
        Tips:
        - Verify the network with *Validate*.
        - The fields of the input layer are preserved. Consider using them to 
        get the diameter and roughness of the pipe.
        ===
        Genera una red epanet a partir de líneas.
        La red generada consiste en dos capas: una de nodos y otra de líneas.
        Los extremos de línea no distanciados más de la tolerancia se fusionan 
        en un nodo. 
        - La capa de nodos contendrá los campos:
        * id * type[1] * elevation (‘type’ en blanco)
        - La capa de línea contendrá los campos:
        * id * start *end * type[2] * length (‘type’ se establece a PIPE, y la 
        longitud se calcula a partir de la capa de entrada.)
        
        Limitaciones:
        - MultiGeometry no es compatible
        - La coordenada Z se ignora
        
        Notas:
         [1] JUNCTION / RESERVOIR / TANK
         [2] PIPE/ CVPIPE/PUMP/PRV/PSV/PBV/FCV/TCV/GPV
        
        Consejos:
        -  Verifique la red con *Validate*.
        - Los campos de la capa de entrada se conservan. Considere usarlos para
        obtener el diámetro y la rugosidad de la tubería.
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Line vector layer input'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.TOLERANCE,
                self.tr('Minimum node separation, otherwise merge them'),
                defaultValue=0.001,
                minValue=0.0001,
                maxValue=1.0
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.NODE_PREFIX,
                self.tr('Node prefix'),
                defaultValue='N-'
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_INIT,
                self.tr('Number of the first node'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1000
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_DELTA,
                self.tr('Node increment'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.LINK_PREFIX,
                self.tr('Link prefix'),
                defaultValue='L-'
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINK_INIT,
                self.tr('Number of first link'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1000
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINK_DELTA,
                self.tr('Link increment'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )

        # ADD NODE AND LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODE_OUTPUT,
                self.tr('Network node layer')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINK_OUTPUT,
                self.tr('Network link layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        linelayer = self.parameterAsSource(parameters, self.INPUT, context)
        tol = self.parameterAsDouble(parameters, self.TOLERANCE, context)
        np = self.parameterAsString(parameters, self.NODE_PREFIX, context)
        ni = self.parameterAsInt(parameters, self.NODE_INIT, context)
        nd = self.parameterAsInt(parameters, self.NODE_DELTA, context)
        lp = self.parameterAsString(parameters, self.LINK_PREFIX, context)
        li = self.parameterAsInt(parameters, self.LINK_INIT, context)
        ld = self.parameterAsInt(parameters, self.LINK_DELTA, context)
        
        # SEND INFORMATION TO THE USER
        feedback.pushInfo('='*40)
        crsid = linelayer.sourceCrs().authid()
        if crsid:
            feedback.pushInfo('CRS is {}.'.format(crsid))
        else:
            feedback.pushInfo('WARNING: CRS is not set!')

        if linelayer.wkbType() == QgsWkbTypes.MultiLineString:
            feedback.reportError('ERROR: Source geometry is MultiLineString!')

        # READ LINESTRINGS AS WKT

        lines = [line.geometry().asWkt() for line in linelayer.getFeatures()]

        # BUILD NETWORK FROM LINES

        newnetwork = tools.Network()
        newnetwork.from_lines(lines, tol, np, ni, nd, lp, li, ld)
        nodes = newnetwork.nodes
        links = newnetwork.links

        # GENERATE NODE LAYER
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
            linelayer.sourceCrs()
            )

        # ADD FEATURES
        ncnt = 0
        f = QgsFeature()
        for node in nodes:
            f.setGeometry(QgsGeometry.fromWkt(node.to_wkt()))
            f.setAttributes([node.nodeid, '', ''])
            node_sink.addFeature(f)
            ncnt += 1

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(50*ncnt/len(nodes))

        # GENERATE LINK LAYER
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("start", QVariant.String))
        newfields.append(QgsField("end", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("length", QVariant.Double))
        newfields.extend(linelayer.fields())
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.LINK_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString,
            linelayer.sourceCrs()
            )

        # ADD FEATURES
        lcnt = 0
        g = QgsFeature()
        for f in linelayer.getFeatures():
            link = links[lcnt]

            # UPDATE GEOMETRY (NODE -> AVERAGE POINT COOORDINATES)
            attr = [link.linkid, link.start, link.end, 'PIPE', link.length]
            attr.extend(f.attributes())
            g.setAttributes(attr)
            g.setGeometry(QgsGeometry.fromWkt(link.to_wkt()))
            link_sink.addFeature(g)
            lcnt += 1

            # SHOW PROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/len(links))
        feedback.pushInfo('Generated network.')
        feedback.pushInfo('Nodes: {}.'.format(ncnt))
        feedback.pushInfo('Links: {}.'.format(lcnt))
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id, self.LINK_OUTPUT: link_id}
