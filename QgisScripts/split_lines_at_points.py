# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsFeatureSink,
                       QgsFeature,
                       QgsFields,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsPoint,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink
                       )
from nettools import Network

class SplitLinesAtPoints(QgsProcessingAlgorithm):
    """
    Split lines at points.
    """

    # DEFINE CONSTANTS
    
    POINTS_INPUT = 'POINTS_INPUT'
    LINES_INPUT = 'LINES_INPUT'
    TOLERANCE_INPUT = 'TOLERANCE_DIST'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return SplitLinesAtPoints()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'Split_lines_at_points'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Split lines at points')

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
        msg = "Split lines at points positions. \n"
        msg += "Use for add 'T', 'X' and n-junction"
        return self.tr(msg)

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """
        
        # INPUT
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POINTS_INPUT,
                self.tr('Input points layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINES_INPUT,
                self.tr('Input lines layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.TOLERANCE_INPUT,
                self.tr('Tolerance distance'),
                defaultValue = 0.01,
                minValue = 0.0,
                maxValue = 100.0
            )
        )
        
        # OUTPUT
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output lines layer')
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        
        pntlayer = self.parameterAsSource(parameters, self.POINTS_INPUT, context)
        linlayer = self.parameterAsSource(parameters, self.LINES_INPUT, context)
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE_INPUT, context)
        
        # OUTPUT
        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            QgsFields(),
            QgsWkbTypes.LineString,
            linlayer.sourceCrs()
            )
        
        # BIND TO SPLIT FUNCTION
        
        split = Network().split_polylines
        
        
        # LOAD POINTS AND LINES
        
        points = []
        lines = []
        
        for f in pntlayer.getFeatures():
            x,y = f.geometry().asPoint().x(),f.geometry().asPoint().y()
            points.append((x,y))
            
        for f in linlayer.getFeatures():
            newline = []
            for vertex in f.geometry().asPolyline():
                x,y = vertex.x(),vertex.y() 
                newline.append((x,y))
                
            lines.append(newline)
                      
        
        # SPLIT LINES 
        
        
        newlines = split(lines, points, tolerance)
        
        for line in newlines:
            #add feature to sink
            polyline = []
            f = QgsFeature()
            for vertex in line:
                x = vertex[0]
                y = vertex[1]
                polyline.append(QgsPoint(x,y))
            f.setGeometry(QgsGeometry.fromPolyline(polyline))
            sink.addFeature(f, QgsFeatureSink.FastInsert) 
        
        
        icnt = linlayer.featureCount()
        fcnt = len(newlines)
        
        msg = 'Split points: {} final line number: {}.'.format(icnt,fcnt)
        feedback.pushInfo(msg)  
        
        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {self.OUTPUT: dest_id}
