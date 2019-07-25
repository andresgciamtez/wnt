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
from qgis.core import (QgsFeatureSink,
                       QgsFeature,
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
    Built a network from 2d lines.
    """

    # DEFINE CONSTANTS
    
    INPUT = 'INPUT'
    MERGE_DIST = 'MERGE_DIST'
    NODE_PREFIX = 'NODE_PREFIX'
    NODE_INIT = 'NODE_INIT'
    NODE_DELTA = 'NODE_DELTA'
    LINK_PREFIX = 'LINK_PREFIX'
    LINK_INIT = 'LINK_INIT'
    LINK_DELTA = 'LINK_DELTA'
    NODES_OUTPUT = 'NODES_OUTPUT'
    LINKS_OUTPUT = 'LINKS_OUTPUT'
    
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
        return self.tr('Water Network tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'wnt'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Build a network (nodes and links) from 2D (poly)lines.')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """
        # INPUT
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input LineString vector layer'),
                types=[QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.MERGE_DIST,
                self.tr('Minimum node separation, also merge them'),
                defaultValue = 0.1,
                minValue = 0.0,
                maxValue = 100.0
            )
        )
        self.addParameter(
                QgsProcessingParameterString(
                self.NODE_PREFIX,
                self.tr('Node prefix'),
                defaultValue = 'N-'
            )
        )       
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_INIT,
                self.tr('Node start number'),
                type = QgsProcessingParameterNumber.Integer,
                defaultValue = 1000
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.NODE_DELTA,
                self.tr('Node number increment'),
                type = QgsProcessingParameterNumber.Integer,
                defaultValue = 10
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.LINK_PREFIX,
                self.tr('Link prefix'),
                defaultValue = 'L-'
            )
        )       
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINK_INIT,
                self.tr('Link start number'),
                type = QgsProcessingParameterNumber.Integer,
                defaultValue = 1000
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.LINK_DELTA,
                self.tr('Link number increment'),
                type = QgsProcessingParameterNumber.Integer,
                defaultValue = 10
            )
        )
        
        # ADD NODE AND LINK FEATURE SINK 
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODES_OUTPUT,
                self.tr('Nodes layer')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINKS_OUTPUT,
                self.tr('Links layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        linelayer = self.parameterAsSource(parameters, self.INPUT, context)
        t = self.parameterAsDouble(parameters, self.MERGE_DIST, context)
        np = self.parameterAsString(parameters, self.NODE_PREFIX, context)
        ni = self.parameterAsInt(parameters, self.NODE_INIT, context)
        nd = self.parameterAsInt(parameters, self.NODE_DELTA, context)
        lp = self.parameterAsString(parameters, self.LINK_PREFIX, context)
        li = self.parameterAsInt(parameters, self.LINK_INIT, context)
        ld = self.parameterAsInt(parameters, self.LINK_DELTA, context)
        
        # SEND INFORMATION TO THE USER

        feedback.pushInfo('CRS is {}'.format(linelayer.sourceCrs().authid()))       
        
        if linelayer.wkbType() == QgsWkbTypes.MultiLineString:
            feedback.pushInfo('Source geometry is MultiLineString!')
            
        # READ LINESTRINGS AS WKT
        
        lines = [line.geometry().asWkt() for line in linelayer.getFeatures()]
        
        # BUILD NETWORK FROM LINES
        
        newnetwork = tools.Network()
        newnetwork.from_lines(lines, t, np, ni, nd, lp, li, ld)
        nodes = newnetwork.nodes
        links = newnetwork.links
        
        # GENERATE NODES LAYER
        newfields = QgsFields()     
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("elevation", QVariant.Double))
        (nodes_sink, nodes_id) = self.parameterAsSink(
            parameters,
            self.NODES_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point,
            linelayer.sourceCrs()
            )
        
        ncnt = 0
        ntot = len(nodes)
        for node in nodes:
            #add feature to sink
            ncnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(node.get_wkt()))
            f.setAttributes([node.nodeid, '', ''])
            nodes_sink.addFeature(f, QgsFeatureSink.FastInsert)
            
            if ncnt % 100 == 0:
                feedback.setProgress(50*ncnt/ntot) # Update the progress bar 
        
        # GENERATE LINKS LAYER
        
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("start", QVariant.String))
        newfields.append(QgsField("end", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("length", QVariant.Double))
        (links_sink, links_id) = self.parameterAsSink(
            parameters,
            self.LINKS_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString,
            linelayer.sourceCrs()
            )

        lcnt = 0
        ltot = len(links)
        for link in links:
            #add feature to sink
            lcnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(link.get_wkt()))
            length = link.get_length2d()
            f.setAttributes([link.linkid, link.start, link.end, 'PIPE', length])
            links_sink.addFeature(f, QgsFeatureSink.FastInsert)
            
            if lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/ltot) # Update the progress bar 
        
        msg = 'Add: {} nodes and {} links.'.format(ncnt,lcnt)
        feedback.pushInfo(msg) 
        
        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {self.NODES_OUTPUT: nodes_id,self.LINKS_OUTPUT: links_id}
