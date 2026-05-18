"""Connect source and target features by distance."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsWkbTypes
                      )
from .base import WntProcessingAlgorithm
from .messages import crs as log_crs
from .messages import error, finish, info, start


class ConnectByDistanceAlgorithm(WntProcessingAlgorithm):
    """
    Connect entities by distance.
    """

    # DEFINE CONSTANTS
    SOURCE_INPUT = 'SOURCE_LAYER_INPUT'
    TARGET_INPUT = 'TARGET_LAYER_INPUT'
    CONNECTION_OUTPUT = 'CONNECTION_OUTPUT'
    MAX_CONNECTIONS = 'MAX_CONNECTIONS'
    MAX_DISTANCE = 'MAX_DISTANCE'



    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ConnectByDistanceAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'connect_by_distance'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Connect by distance'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return 'Demand'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'demand'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''<p>Connects features from a <b>source layer</b> to a <b>target layer</b> by minimum distance.</p>
<ul>
<li>Both layers must contain an <code>id</code> field.</li>
<li>The maximum number of connections and maximum distance limit the generated links.</li>
<li>The output is a line layer representing the connections.</li>
</ul>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SOURCE_INPUT,
                self.tr('Source layer'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
                )
            )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET_INPUT,
                self.tr('Target layer'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
                )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_CONNECTIONS,
                self.tr('Max number of connections'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_DISTANCE,
                self.tr('Max distance'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0
                )
            )

        # ADD LINKS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.CONNECTION_OUTPUT,
                self.tr('Connection layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        s_ly = self.parameterAsSource(parameters, self.SOURCE_INPUT, context)
        t_ly = self.parameterAsSource(parameters, self.TARGET_INPUT, context)
        max_con = self.parameterAsInt(parameters, self.MAX_CONNECTIONS, context)
        max_dst = self.parameterAsDouble(parameters, self.MAX_DISTANCE, context)

        # CHECK CRS
        crs = s_ly.sourceCrs()
        if crs == t_ly.sourceCrs():

            # SEND INFORMATION TO THE USER
            start(feedback, self.displayName())
            log_crs(feedback, crs)
        else:
            error(feedback, "Layers have different CRS")
            return {}

        # OUTPUT LAYER
        fields= QgsFields()
        fields.append(QgsField('source', QMetaType.QString))
        fields.append(QgsField('target', QMetaType.QString))
        fields.append(QgsField('distance', QMetaType.Double))
        fields.append(QgsField('n', QMetaType.Int))
        (connection_sink, connection_id) = self.parameterAsSink(
            parameters,
            self.CONNECTION_OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            crs
            )

        # COMPUTE AND WRITE LINK LAYER
        f = QgsFeature()
        cnt = 0
        for source in s_ly.getFeatures():
            possible_connections = []
            for target in t_ly.getFeatures():
                geometry = source.geometry().shortestLine(target.geometry())
                distance = geometry.length()
                if distance <= max_dst:
                    connection = [geometry]
                    connection.append(source["id"])
                    connection.append(target["id"])
                    connection.append(distance)
                    possible_connections.append(connection)
            possible_connections.sort(key=lambda d: d[-1])
            connections = possible_connections[:max_con]
            for connection in connections:
                connection.append(len(connections))
                f.setGeometry(connection[0])
                f.setAttributes(connection[1:])
                connection_sink.addFeature(f)
                cnt += 1

            # SHOW PROGRESS
            feedback.setProgress(100*cnt/s_ly.featureCount())

        # SHOW PROGRESS
        info(feedback, "Source features", s_ly.featureCount())
        info(feedback, "Target features", t_ly.featureCount())
        info(feedback, "Connections", cnt)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.CONNECTION_OUTPUT: connection_id}

