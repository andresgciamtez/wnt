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
                       QgsProcessingParameterFeatureSource,
                       QgsPointXY
                      )
from . import utils_core as tools

class NetworkFromLinesAlgorithm(QgsProcessingAlgorithm):
    """
    Built a network from lines.
    """

    # DEFINE CONSTANTS
    INPUT = 'INPUT'
    TOLERANCE = 'TOLERANCE'
    NODE_MASK = 'NODE_MASK'
    NODE_INI = 'NODE_INI'
    NODE_INC = 'NODE_INC'
    LINK_MASK = 'LINK_MASK'
    LINK_INI = 'LINK_INI'
    LINK_INC = 'LINK_INC'
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
        The node layer contains the fields: *id *type *elevation
        The line layer contains the fields: *id *start *end *type *length
        
        Limitations:
        - MultiGeometry is not supported
        - The Z coordinate is ignored
        
        Notes:
        - Looped (start = end) generates an error
        - *type and *elevation in nodes are not set
        - *type' in nodes is set to 'PIPE'
        - Epanet node types: JUNCTION/RESERVOIR/TANK
        - Epanet link types: PIPE/CVPIPE/PUMP/PRV/PSV/PBV/FCV/TCV/GPV
        
        Tips:
        - Verify the network with *Validate*
        - The fields of the input layer are preserved. Consider using them to 
        get the diameter and roughness of the pipe
        
        ===
        Genera una red epanet a partir de líneas.
        La red generada consiste en dos capas: una de nodos y otra de líneas.
        Los extremos de línea no distanciados más de la tolerancia se fusionan 
        en un nodo. 
        La capa de nodos contendrá los campos: *id *type *elevation
        La capa de línea contendrá los campos: *id *start *end *type *length
        
        Limitaciones:
        - No se acepta MultiGeometry
        - La coordenada Z se ignora
        
        Notas:
        - Líneas en bucle (start = end) generan un error 
        - *type y *elevation en la capa de nodos deben asignarse a posteriori
        - *type en la capa de líneas se fija en 'PIPE'
        - Epanet node types: JUNCTION/RESERVOIR/TANK
        - Epanet link types: PIPE/CVPIPE/PUMP/PRV/PSV/PBV/FCV/TCV/GPV
        
        Consejos:
        -  Verifique la red con *Validate*
        - Los campos de la capa de entrada se conservan. Considere usarlos para
        obtener el diámetro y la rugosidad de la tubería
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
                self.NODE_MASK,
                self.tr('Node mask (P-$$-S generates P-01-S)'),
                defaultValue='$'
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_INI,
                self.tr('Number of the first node'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_INC,
                self.tr('Node increment'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.LINK_MASK,
                self.tr('Link mask (P-$$-S generates P-01-S)'),
                defaultValue='$'
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINK_INI,
                self.tr('Number of first link'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINK_INC,
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
        nmask = self.parameterAsString(parameters, self.NODE_MASK, context)
        nini = self.parameterAsInt(parameters, self.NODE_INI, context)
        ninc = self.parameterAsInt(parameters, self.NODE_INC, context)
        lmask = self.parameterAsString(parameters, self.LINK_MASK, context)
        lini = self.parameterAsInt(parameters, self.LINK_INI, context)
        linc = self.parameterAsInt(parameters, self.LINK_INC, context)

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
        lines = []
        for feature in linelayer.getFeatures():
            line = []
            for point in feature.geometry().asPolyline():
                line.append((point.x(), point.y()))
            lines.append(line)
        for line in lines:
            if tools.dist2p(line[0], line[-1]) < tol:
                feedback.reportError('ERROR: Looped LineString!')
                return {}

        # SHOW INFO
        feedback.pushInfo('Read: {} LineStrings.'.format(len(lines)))

        # CONFIG
        def n_format(index):
            return tools.format_id(nini + index*ninc, nmask)

        def l_format(index):
            return tools.format_id(lini + index*linc, lmask)

        # CALCULATE NETWORK
        nodes, links = tools.net_from_linestrings(lines, tol)

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
        for x, y in nodes[:]:
            nodeid = n_format(ncnt)
            f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
            f.setAttributes([nodeid, '', 0.0])
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
            linkid = l_format(lcnt)
            start = n_format(link[0])
            end = n_format(link[1])
            poly = []
            for x, y in links[lcnt][2][:]:
                poly.append(QgsPointXY(x, y))
            length = tools.length2d(poly)
            attr = [linkid, start, end, 'PIPE', length]
            attr.extend(f.attributes())
            g.setGeometry(QgsGeometry.fromPolylineXY(poly))
            g.setAttributes(attr)
            link_sink.addFeature(g)
            lcnt += 1

            # SHOW PROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/len(links))
        feedback.pushInfo('Network was generated successfully.')
        feedback.pushInfo('Node number: {}.'.format(ncnt))
        feedback.pushInfo('Link number: {}.'.format(lcnt))
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id, self.LINK_OUTPUT: link_id}
