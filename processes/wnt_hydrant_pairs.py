"""Create hydrant pair connection lines."""

from qgis.PyQt.QtCore import QVariant
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
                       QgsWkbTypes
                      )
from .base import WntProcessingAlgorithm
from .messages import crs as log_crs
from .messages import finish, info, start

class HydrantPairsAlgorithm(WntProcessingAlgorithm):
    """
    Built a network from lines.
    """

    # DEFINE CONSTANTS
    HYD_INPUT = 'HYDRANT_INPUT'
    ID_FIELD = 'HIDRANT_ID_FIELD'
    MAX_DIST = 'MAX_DIST'
    PAIRS_OUTPUT = 'PAIRS_OUTPUT'


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
        return 'Hydrant pairs'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return 'Fire'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'fire'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''<p>Creates hydrant pairs from a hydrant node layer.</p>
<ul>
<li>The output is a line layer connecting paired hydrants.</li>
<li>The line geometry helps verify that pairs can be connected through public space.</li>
<li>Hydrants farther apart than the maximum separation are ignored.</li>
</ul>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.HYD_INPUT,
                self.tr('Hydrant layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                self.tr('Hydrant ID field'),
                'id',
                self.HYD_INPUT
                )
            )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.MAX_DIST,
                self.tr('Maximum hydrant separation'),
                defaultValue=200,
                minValue=0.1,
                maxValue=10000
                )
            )
        # ADD PAIRS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PAIRS_OUTPUT,
                self.tr('Hydrant pairs layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        hydlayer = self.parameterAsSource(parameters, self.HYD_INPUT, context)
        idfield = self.parameterAsString(parameters, self.ID_FIELD, context)
        maxdist = self.parameterAsDouble(parameters, self.MAX_DIST, context)

        # SEND INFORMATION TO THE USER
        start(feedback, self.displayName())
        log_crs(feedback, hydlayer.sourceCrs())

        # READ HYDRANTS
        hydrants = []
        pairs = []
        for f in hydlayer.getFeatures():
            hydrants.append((f[idfield], f.geometry().asPoint()))

        # CALCULATE PAIRS
        for i in range(len(hydrants)-1):
            for j in range(i+1, len(hydrants)):
                dist = hydrants[i][1].distance(hydrants[j][1])
                if dist <= maxdist:
                    pairs.append((hydrants[i], hydrants[j], dist))

        # SHOW INFO
        info(feedback, "Input hydrants", len(hydrants))

        # GENERATE PAIRS LAYER
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.String))
        fields.append(QgsField("hydrant_1", QVariant.String))
        fields.append(QgsField("hydrant_2", QVariant.String))
        fields.append(QgsField("distance", QVariant.Double))
        (pairs_sink, pairs_id) = self.parameterAsSink(
            parameters,
            self.PAIRS_OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            hydlayer.sourceCrs()
            )

        # SHOW PROGRESS
        feedback.setProgress(50)

        # ADD FEATURES
        f = QgsFeature()
        cnt = 0
        for pair in pairs:
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

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.PAIRS_OUTPUT: pairs_id}
