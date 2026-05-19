"""Split line features at point locations."""

from math import dist, hypot
from qgis.core import (Qgis,
                       QgsFeature,
                       QgsGeometry,
                       QgsWkbTypes,
                       QgsPointXY,
                       QgsProcessing,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink
                       )
from .base import WntProcessingAlgorithm
from .messages import crs as log_crs
from .messages import error, finish, info, start


def _splitter_for_point(geometry, point, tolerance):
    sqr_dist, nearest, next_vertex, _ = geometry.closestSegmentWithContext(point)
    if sqr_dist < 0 or sqr_dist > tolerance * tolerance:
        return None

    vertices = list(geometry.vertices())
    if next_vertex <= 0 or next_vertex >= len(vertices):
        return None

    previous = vertices[next_vertex - 1]
    following = vertices[next_vertex]
    dx = following.x() - previous.x()
    dy = following.y() - previous.y()
    length = hypot(dx, dy)
    if length == 0:
        return None

    offset = max(tolerance * 2, length * 1e-6, 1e-9)
    nx = -dy / length * offset
    ny = dx / length * offset
    return [
        QgsPointXY(nearest.x() - nx, nearest.y() - ny),
        QgsPointXY(nearest.x() + nx, nearest.y() + ny),
    ]


def _split_geometry_at_points(geometry, points, tolerance):
    parts = [QgsGeometry(geometry)]
    for point in points:
        point_xy = QgsPointXY(point[0], point[1])
        point_geometry = QgsGeometry.fromPointXY(point_xy)
        new_parts = []
        for part in parts:
            if part.distance(point_geometry) > tolerance:
                new_parts.append(part)
                continue

            splitter = _splitter_for_point(part, point_xy, tolerance)
            if splitter is None:
                new_parts.append(part)
                continue

            result, split_parts, _ = part.splitGeometry(splitter, False)
            if result == Qgis.GeometryOperationResult.Success and split_parts:
                new_parts.append(part)
                new_parts.extend(split_parts)
            else:
                new_parts.append(part)
        parts = new_parts

    return parts if len(parts) > 1 else None


def _feature_with_geometry(feature, geometry):
    try:
        new_feature = QgsFeature(feature)
    except TypeError:
        new_feature = feature
    new_feature.setGeometry(geometry)
    return new_feature

class SplitLinesAtPointsAlgorithm(WntProcessingAlgorithm):
    """
    Split lines at points.
    """

    # DEFINE CONSTANTS
    INPUT_POINTS = 'INPUT_POINTS'
    INPUT_LINES = 'INPUT_LINES'
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
                self.INPUT_POINTS,
                self.tr('Input point layer'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
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
        pntlayer = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        linlayer = self.parameterAsSource(parameters, self.INPUT_LINES, context)
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
        cnt = 0                         # output link counter
        tot = linlayer.featureCount()
        processed = 0                   # input feature counter
        # LINES LOOP
        for f in linlayer.getFeatures():
            x1 = y1 = 1e24               # initialize x boundbox
            x2 = y2 = -1e24              # initialize y boundbox
            for vertex in f.geometry().asPolyline():
                x, y = vertex.x(), vertex.y()

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
                splitted = _split_geometry_at_points(f.geometry(), fpoints, tolerance)
                if splitted:

                    # ADD NEW LINESTRINGS
                    for geometry in splitted:
                        sink.addFeature(_feature_with_geometry(f, geometry))
                        cnt += 1
                else:

                    # KEEP ORIGINAL FEATURE
                    sink.addFeature(f)
                    cnt += 1
            else:

                # KEEP ORIGINAL FEATURE
                sink.addFeature(f)
                cnt += 1

            processed += 1
            # SHOW PROGRESS
            if tot > 0:
                feedback.setProgress(100*processed/tot) # Update the progress bar

        info(feedback, "Input lines", tot)
        info(feedback, "Output lines", cnt)
        finish(feedback)

        # PROCCES CANCELED

        if feedback.isCanceled():
            return {}

        # OUTPUT

        return {self.OUTPUT: dest_id}
