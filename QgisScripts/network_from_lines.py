# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
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
from nettools import Network
 
class NetworkFromLines(QgsProcessingAlgorithm):
    """
    Built a network from 2d lines.
    
    Return
    ------
    A Links LineString vector layer. Fields: id, start, end, type, length.
    A Nodes Point vector layer. Fields: id, type, elevation. 
    """
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
        return NetworkFromLines()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'networkfromlines'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Build a network from lines')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Net tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'nettools'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Build a network (nodes and links) from 2D (poly)lines.')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """
        # 'INPUT' is the recommended name for the main input parameter.
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
        Run the process.
        """
        # INPUT
        input = self.parameterAsSource(parameters, self.INPUT, context)
        t = self.parameterAsDouble(parameters, self.MERGE_DIST, context)
        np = self.parameterAsString(parameters, self.NODE_PREFIX, context)
        ni = self.parameterAsInt(parameters, self.NODE_INIT, context)
        nd = self.parameterAsInt(parameters, self.NODE_DELTA, context)
        lp = self.parameterAsString(parameters, self.LINK_PREFIX, context)
        li = self.parameterAsInt(parameters, self.LINK_INIT, context)
        ld = self.parameterAsInt(parameters, self.LINK_DELTA, context)
        
        # SEND INFORMATION TO THE USER
        feedback.pushInfo('*'*4)
        feedback.pushInfo('CRS is {}'.format(input.sourceCrs().authid()))       
        if input.wkbType() == QgsWkbTypes.MultiLineString:
            feedback.pushInfo('Source geometry is MultiLineString!')
            #raise QgsProcessingException('Source geometry is MultiLineString!')
            
        # READ LINESTRINGS AS WKT
        lines = [line.geometry().asWkt() for line in input.getFeatures()]
        
        # BUILD NETWORK FROM LINES
        newnetwork = Network()
        newnetwork.from_lines(lines, t, np, ni, nd, lp, li, ld)
        nodes,links = newnetwork.nodes,newnetwork.links
        msg = '# nodes: {}, # links: {}.'.format(len(nodes),len(links))
        feedback.pushInfo(msg)
        
        # GENERATE NODES LAYER
        newfields = QgsFields()     
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("elevation", QVariant.Double))
        (nodes_sink, nodes_dest_id) = self.parameterAsSink(
            parameters,
            self.NODES_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point,
            input.sourceCrs()
            )
        for node in nodes:
            #add feature to sink
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(node.get_wkt()))
            f.setAttributes([node.nodeid, '', ''])
            nodes_sink.addFeature(f, QgsFeatureSink.FastInsert)
        
        # GENERATE LINKS LAYER
        
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("start", QVariant.String))
        newfields.append(QgsField("end", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("length", QVariant.Double))
        (links_sink, links_dest_id) = self.parameterAsSink(
            parameters,
            self.LINKS_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString,
            input.sourceCrs()
            )

        for link in links:
            #add feature to sink
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(link.get_wkt()))
            length = link.get_length()
            f.setAttributes([link.linkid, link.start, link.end, 'PIPE', length])
            links_sink.addFeature(f, QgsFeatureSink.FastInsert) 
        
        feedback.pushInfo('*'*4)
        
        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {'NODES_OUTPUT': nodes_dest_id,'LINKS_OUTPUT': links_dest_id}