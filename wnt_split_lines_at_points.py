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

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsGeometry,
                       QgsWkbTypes,
                       QgsPoint,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink
                       )
from . import tools

class SplitLinesAtPointsAlgorithm(QgsProcessingAlgorithm):
    """
    Split lines at points.
    """

    # DEFINE CONSTANTS
    POINT_INPUT = 'POINT_INPUT'
    LINE_INPUT = 'LINE_INPUT'
    TOLERANCE = 'TOLERANCE'
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
        return SplitLinesAtPointsAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'split_lines_at_points'

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
        return self.tr('Modify')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'modify'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        msg = "Split lines at point positions. \n"
        msg += "Use for add 'T', 'X' and n-junction."
        return self.tr(msg)

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        #   DEFINE INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.POINT_INPUT,
                self.tr('Input point layer'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINE_INPUT,
                self.tr('Input line layer'),
                [QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.TOLERANCE,
                self.tr('Tolerance distance'),
                defaultValue=0.001,
                minValue=0.0001,
                maxValue=1.0
                )
            )

        # DEFINE OUTPUT
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Splitted line layer')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        pntlayer = self.parameterAsSource(parameters, self.POINT_INPUT, context)
        linlayer = self.parameterAsSource(parameters, self.LINE_INPUT, context)
        tolerance = self.parameterAsDouble(parameters, self.TOLERANCE, context)

        # CHECK CRS
        crs = pntlayer.sourceCrs()
        if crs == linlayer.sourceCrs():

            # SEND INFORMATION TO THE USER
            feedback.pushInfo('='*40)
            feedback.pushInfo('CRS is {}'.format(crs.authid()))
        else:
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

        # OUTPUT
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            linlayer.fields(),
            QgsWkbTypes.LineString,
            linlayer.sourceCrs()
            )

        # LOAD AND FILTER OVERLAPPED POINTS
        points = []
        for f in pntlayer.getFeatures():
            x, y = f.geometry().asPoint().x(), f.geometry().asPoint().y()
            mindist = 1e24
            for point in points:
                mindist = min(mindist, tools.dist_2_p((x, y), point))
            if mindist > tolerance:
                points.append((x, y))

        # SHOW PROGRESS
        msg = 'Final splitting points: {}. Discarted overlapped points: {}.'
        msg = msg.format(len(points), pntlayer.featureCount() - len(points))
        feedback.pushInfo(msg)

        # LOAD AND SPLIT LINES
        cnt = 0                         # link counter
        tot = linlayer.featureCount()
        x1 = y1 = 1e24                   # initialize x boundbox
        x2 = y2 = -1e24                  # initialize y boundbox

        # LINES LOOP
        for f in linlayer.getFeatures():
            line = []
            for vertex in f.geometry().asPolyline():
                x, y = vertex.x(), vertex.y()
                line.append((x, y))

                # CALCULATE BOUNDBOX
                x1, y1 = min(x1, x), min(y1, y)
                x2, y2 = max(x2, x), max(y2, y)
            x1, y1 = x1-tolerance, y1-tolerance
            x2, y2 = x2+tolerance, y2+tolerance

            # FILTER POINTS
            fpoints = []
            for point in points:
                if x1 <= point[0] <= x2 and y1 <= point[1] <= y2:
                    fpoints.append(point)
           # SPLIT
            if fpoints:
                splitted = tools.split_linestring_m(line, fpoints, tolerance)
                if splitted:

                    # ADD NEW LINESTRINGS
                    for part in splitted:
                        newpolyline = []
                        for vertex in part:
                            x, y = vertex[0:2]
                            newpolyline.append(QgsPoint(x, y))
                        f.setGeometry(QgsGeometry.fromPolyline(newpolyline))
                        sink.addFeature(f)
                        cnt += 1
            else:

                # KEEP ORIGINAL FEATURE
                sink.addFeature(f)
                cnt += 1

            # SHOW PROGRESS
            feedback.setProgress(100*cnt/tot) # Update the progress bar

        msg = 'Final line number: {}. From: {}.'
        feedback.pushInfo(msg.format(cnt, tot))
        feedback.pushInfo('='*40)

        # PROCCES CANCELED

        if feedback.isCanceled():
            return {}

        # OUTPUT

        return {self.OUTPUT: dest_id}
