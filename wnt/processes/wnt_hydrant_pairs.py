"""Create hydrant pair connection lines."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsPoint,
                       QgsLineString,
                       QgsProcessing,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsRectangle,
                       QgsSpatialIndex,
                       QgsWkbTypes
                      )
from .base import WntProcessingAlgorithm, require_projected_crs
from .messages import crs as log_crs
from .messages import finish, info, start

class HydrantPairsAlgorithm(WntProcessingAlgorithm):
    """
    Generate hydrant pairs within a maximum separation.
    """

    # DEFINE CONSTANTS
    INPUT_HYDRANTS = 'INPUT_HYDRANTS'
    FIELD_ID = 'FIELD_ID'
    MAX_DISTANCE = 'MAX_DISTANCE'
    OUTPUT_PAIRS = 'OUTPUT_PAIRS'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return HydrantPairsAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'hydrant_pairs'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Hydrant pairs')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Fire')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'fire'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''<p>Creates hydrant pairs/calculation scenarios from a hydrant layer.</p>
<ul>
<li>The output is a line layer connecting paired hydrants/fire scenarios.</li>
<li>The line geometry helps verify that pairs can be connected through public space.</li>
<li>Pairs farther apart than the maximum separation are not generated.</li>
</ul>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_HYDRANTS,
                self.tr('Hydrant layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_ID,
                self.tr('Hydrant ID field'),
                'id',
                self.INPUT_HYDRANTS
                )
            )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.MAX_DISTANCE,
                self.tr('Maximum hydrant separation'),
                defaultValue=200,
                parentParameterName=self.INPUT_HYDRANTS,
                minValue=0.1,
                maxValue=10000
                )
            )
        # ADD PAIRS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_PAIRS,
                self.tr('Hydrant pairs layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        hydlayer = self.parameterAsSource(parameters, self.INPUT_HYDRANTS, context)
        idfield = self.parameterAsString(parameters, self.FIELD_ID, context)
        maxdist = self.parameterAsDouble(parameters, self.MAX_DISTANCE, context)

        crs = hydlayer.sourceCrs()
        require_projected_crs(crs, feedback)

        # SEND INFORMATION TO THE USER
        start(feedback, self.displayName())
        log_crs(feedback, crs)

        # READ HYDRANTS
        hydrant_features = list(hydlayer.getFeatures())
        hydrants = [(f[idfield], f.geometry().asPoint(), f.id()) for f in hydrant_features]
        pairs = []

        # CALCULATE PAIRS
        try:
            index = QgsSpatialIndex(iter(hydrant_features))
        except (TypeError, RuntimeError):
            index = None

        if index is None:
            for i in range(len(hydrants)-1):
                for j in range(i+1, len(hydrants)):
                    dist = hydrants[i][1].distance(hydrants[j][1])
                    if dist <= maxdist:
                        pairs.append((hydrants[i], hydrants[j], dist))
        else:
            by_fid = {f.id(): item for f, item in zip(hydrant_features, hydrants)}
            seen = set()
            for left in hydrants:
                point = left[1]
                try:
                    bbox = QgsRectangle(
                        point.x() - maxdist,
                        point.y() - maxdist,
                        point.x() + maxdist,
                        point.y() + maxdist,
                    )
                    candidate_ids = index.intersects(bbox)
                except AttributeError:
                    candidate_ids = [item[2] for item in hydrants]
                for fid in candidate_ids:
                    right = by_fid.get(fid)
                    if right is None or left[2] == right[2]:
                        continue
                    key = tuple(sorted((left[2], right[2])))
                    if key in seen:
                        continue
                    seen.add(key)
                    dist = left[1].distance(right[1])
                    if dist <= maxdist:
                        pairs.append((left, right, dist))

        # SHOW INFO
        info(feedback, "Input hydrants", len(hydrants))

        # GENERATE PAIRS LAYER
        fields = QgsFields()
        fields.append(QgsField("id", QMetaType.QString))
        fields.append(QgsField("hydrant_1", QMetaType.QString))
        fields.append(QgsField("hydrant_2", QMetaType.QString))
        fields.append(QgsField("distance", QMetaType.Double))
        (pairs_sink, pairs_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_PAIRS,
            context,
            fields,
            QgsWkbTypes.LineString,
            hydlayer.sourceCrs()
            )

        # SHOW PROGRESS
        feedback.setProgress(50)

        # ADD FEATURES
        cnt = 0
        for pair in pairs:
            f = QgsFeature(fields)
            p1 = QgsPoint(pair[0][1])
            p2 = QgsPoint(pair[1][1])
            f.setGeometry(QgsLineString([p1, p2]))
            f.setAttributes([str(cnt), pair[0][0], pair[1][0], pair[2]])
            pairs_sink.addFeature(f)
            cnt += 1

        # SHOW PROGRESS
        feedback.setProgress(100)
        info(feedback, "Pairs", cnt)
        finish(feedback)

        # PROCESS CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_PAIRS: pairs_id}
