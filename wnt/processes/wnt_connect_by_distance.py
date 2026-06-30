"""Connect source and target features by distance."""

from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessing,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsSpatialIndex,
                       QgsWkbTypes
                      )
from .base import WntProcessingAlgorithm, missing_fields, require_projected_crs, set_progress
from .messages import crs as log_crs
from .messages import error, finish, info, start


class ConnectByDistanceAlgorithm(WntProcessingAlgorithm):
    """
    Connect entities by distance.
    """

    # DEFINE CONSTANTS
    INPUT_SOURCE = 'INPUT_SOURCE'
    INPUT_TARGET = 'INPUT_TARGET'
    OUTPUT_CONNECTIONS = 'OUTPUT_CONNECTIONS'
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
        return self.tr('Connect by distance')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Demand')

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
                self.INPUT_SOURCE,
                self.tr('Source layer'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
                )
            )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_TARGET,
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
            QgsProcessingParameterDistance(
                self.MAX_DISTANCE,
                self.tr('Max distance'),
                defaultValue=0,
                parentParameterName=self.INPUT_SOURCE
                )
            )

        # ADD LINKS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_CONNECTIONS,
                self.tr('Connection layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        s_ly = self.parameterAsSource(parameters, self.INPUT_SOURCE, context)
        t_ly = self.parameterAsSource(parameters, self.INPUT_TARGET, context)
        max_con = self.parameterAsInt(parameters, self.MAX_CONNECTIONS, context)
        max_dst = self.parameterAsDouble(parameters, self.MAX_DISTANCE, context)

        # CHECK CRS
        crs = s_ly.sourceCrs()
        if crs == t_ly.sourceCrs():

            # SEND INFORMATION TO THE USER
            if not require_projected_crs(crs, feedback):
                return {}
            start(feedback, self.displayName())
            log_crs(feedback, crs)
        else:
            error(feedback, "Layers have different CRS")
            return {}

        source_missing = missing_fields(s_ly, ['id'])
        if source_missing:
            error(feedback, "Source layer is missing required fields: " + ", ".join(source_missing))
            return {}
        target_missing = missing_fields(t_ly, ['id'])
        if target_missing:
            error(feedback, "Target layer is missing required fields: " + ", ".join(target_missing))
            return {}
        if max_con <= 0:
            error(feedback, "Max number of connections must be greater than zero")
            return {}
        if max_dst < 0:
            error(feedback, "Max distance must be zero or greater")
            return {}

        # OUTPUT LAYER
        fields= QgsFields()
        fields.append(QgsField('source', QMetaType.QString))
        fields.append(QgsField('target', QMetaType.QString))
        fields.append(QgsField('distance', QMetaType.Double))
        fields.append(QgsField('n', QMetaType.Int))
        (connection_sink, connection_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_CONNECTIONS,
            context,
            fields,
            QgsWkbTypes.LineString,
            crs
            )

        # COMPUTE AND WRITE LINK LAYER
        target_features = list(t_ly.getFeatures())
        target_features_by_id = {feature.id(): feature for feature in target_features}
        target_index = None
        if target_features:
            try:
                target_index = QgsSpatialIndex(iter(target_features))
            except (TypeError, RuntimeError):
                target_index = None

        def candidate_targets(source):
            geometry = source.geometry()
            if target_index is None or not hasattr(geometry, 'boundingBox'):
                return target_features
            bbox = geometry.boundingBox()
            bbox.grow(max_dst)
            return [target_features_by_id[fid] for fid in target_index.intersects(bbox)
                    if fid in target_features_by_id]

        cnt = 0
        total_source = s_ly.featureCount()
        for processed, source in enumerate(s_ly.getFeatures(), start=1):
            if feedback.isCanceled():
                return {}

            possible_connections = []
            for target in candidate_targets(source):
                geometry = source.geometry().shortestLine(target.geometry())
                distance = geometry.length()
                if distance <= max_dst:
                    possible_connections.append([
                        geometry,
                        source["id"],
                        target["id"],
                        distance,
                    ])
            possible_connections.sort(key=lambda d: d[-1])
            connections = possible_connections[:max_con]
            for connection in connections:
                connection.append(len(connections))
                f = QgsFeature(fields)
                f.setGeometry(connection[0])
                f.setAttributes(connection[1:])
                connection_sink.addFeature(f)
                cnt += 1

            # SHOW PROGRESS
            set_progress(feedback, 0, 100, processed, total_source)

        # SHOW PROGRESS
        info(feedback, "Source features", total_source)
        info(feedback, "Target features", t_ly.featureCount())
        info(feedback, "Connections", cnt)
        finish(feedback)

        # OUTPUT
        return {self.OUTPUT_CONNECTIONS: connection_id}
