"""Split line features at point locations."""

from math import dist
from qgis.core import (QgsGeometry,
                       QgsWkbTypes,
                       QgsPoint,
                       QgsProcessing,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink
                       )
from .base import WntProcessingAlgorithm
from ..utils import split
from .messages import crs as log_crs
from .messages import error, finish, info, start

class SplitLinesAtPointsAlgorithm(WntProcessingAlgorithm):
    """
    Split lines at points.
    """

    # DEFINE CONSTANTS
    POINT_INPUT = 'POINT_INPUT'
    LINE_INPUT = 'LINE_INPUT'
    TOLERANCE = 'TOLERANCE'
    OUTPUT = 'OUTPUT'


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
        return 'Split lines at points'

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return 'Modify'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'modify'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''<p>Splits line features at point positions.</p>
<ul>
<li>Use this algorithm to insert junctions or intermediate nodes into line layers.</li>
<li>Points are matched to lines using the tolerance distance.</li>
</ul>
        ''')

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
                self.tr('Split line layer')
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
            start(feedback, self.displayName())
            log_crs(feedback, crs)
        else:
            error(feedback, "Layers have different CRS")
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
                mindist = min(mindist, dist((x, y), point))
            if mindist > tolerance:
                points.append((x, y))

        # SHOW PROGRESS
        info(feedback, "Splitting points", len(points))
        info(feedback, "Overlapped points", pntlayer.featureCount() - len(points))

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
                splitted = split.split_linestring_m(line, fpoints, tolerance)
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

        info(feedback, "Input lines", tot)
        info(feedback, "Output lines", cnt)
        finish(feedback)

        # PROCCES CANCELED

        if feedback.isCanceled():
            return {}

        # OUTPUT

        return {self.OUTPUT: dest_id}
