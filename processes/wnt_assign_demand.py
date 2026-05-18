"""Assign demand sources to target network nodes."""

from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsPoint,
                       QgsLineString,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsWkbTypes,
                       QgsSpatialIndex
                      )
from .base import WntProcessingAlgorithm
from .messages import crs as log_crs
from .messages import error, finish, info, start

class AssignDemandAlgorithm(WntProcessingAlgorithm):
    """
    Assignate demands.
    """

    # DEFINE CONSTANTS
    SOURCE_INPUT = 'SOURCE_LAYER_INPUT'
    SOURCE_FIELDS = 'SOURCE_FIELDS'
    TARGET_INPUT = 'TARGET_LAYER_INPUT'
    ASSIGN_OUTPUT = 'ASSIGNMENT_LAYER_OUTPUT'
    OUTPUT_NODES = 'OUTPUT_NODES'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return AssignDemandAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'assign_demand'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Assign demand'

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
        return self.tr('''<p>Assigns demand from a <b>source layer</b> to a <b>target node layer</b> using the nearest target feature.</p>
<ul>
<li>Both input layers must contain an <code>id</code> field.</li>
<li>The selected source demand fields are copied and accumulated in the target layer.</li>
<li>The output assignment layer stores the connection lines between source and target features.</li>
</ul>
<p>Use <b>Update assignment</b> after editing assignment lines.</p>
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
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.SOURCE_FIELDS,
                self.tr('Source demand fields'),
                None,
                self.SOURCE_INPUT,
                allowMultiple=True
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET_INPUT,
                self.tr('Target layer'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )

        # ADD PAIRS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ASSIGN_OUTPUT,
                self.tr('Assignment layer')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('Target with demands layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        slayer = self.parameterAsSource(parameters, self.SOURCE_INPUT, context)
        sfields = self.parameterAsFields(parameters, self.SOURCE_FIELDS, context)
        tlayer = self.parameterAsSource(parameters, self.TARGET_INPUT, context)

        # CHECK CRS
        crs = slayer.sourceCrs()
        if crs != tlayer.sourceCrs():
            error(feedback, "Layers have different CRS")
            return {}

        # SEND INFORMATION TO THE USER
        start(feedback, self.displayName())
        log_crs(feedback, crs)

        # OUTPUT LAYERS DEFINITION
        fields = QgsFields()
        fields.append(QgsField('source', QVariant.String))
        fields.append(QgsField('target', QVariant.String))
        for field in sfields:
            fields.append(QgsField(field, QVariant.Double))

        (assignment_sink, assignment_id) = self.parameterAsSink(
            parameters,
            self.ASSIGN_OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            crs
        )

        tfields = tlayer.fields()
        node_fields = QgsFields(tfields)
        for field in sfields:
            node_fields.append(QgsField(field, QVariant.Double))

        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            node_fields,
            QgsWkbTypes.Point,
            crs
        )

        # FETCH FIELD INDICES
        t_id_idx = tlayer.fields().lookupField('id')
        s_id_idx = slayer.fields().lookupField('id')
        s_field_indices = {field: slayer.fields().lookupField(field) for field in sfields}

        # SPATIAL INDEX FOR TARGET LAYER
        feedback.pushInfo("Building spatial index for target layer...")
        t_index = QgsSpatialIndex(tlayer.getFeatures())

        # MAP FOR TARGET FEATURES (to avoid re-fetching)
        t_features = {f.id(): f for f in tlayer.getFeatures()}

        # ASSIGN, ACCUMULATE AND WRITE ASSIGNMENT LAYER
        values = {} # key: (target_id, field_name)
        for tfeature in t_features.values():
            t_id = tfeature.attributes()[t_id_idx]
            for field in sfields:
                values[(t_id, field)] = 0.0

        assignment_features = []
        cnt = 0
        total_s = slayer.featureCount()
        for sfeature in slayer.getFeatures():
            s_geom = sfeature.geometry()
            sxy = s_geom.asPoint()

            # Use spatial index to find the nearest neighbor
            nearest_ids = t_index.nearestNeighbor(sxy, 1)
            if not nearest_ids:
                continue

            cfeature = t_features[nearest_ids[0]]
            c_id = cfeature.attributes()[t_id_idx]
            s_id = sfeature.attributes()[s_id_idx]

            f = QgsFeature(fields)
            spoint = QgsPoint(sxy)
            cpoint = QgsPoint(cfeature.geometry().asPoint())
            f.setGeometry(QgsLineString([spoint, cpoint]))

            attr = [s_id, c_id]
            for field in sfields:
                s_val = sfeature.attributes()[s_field_indices[field]]
                attr.append(s_val)
                values[(c_id, field)] += s_val

            f.setAttributes(attr)
            assignment_features.append(f)
            cnt += 1

            if len(assignment_features) >= 200:
                assignment_sink.addFeatures(assignment_features)
                assignment_features = []

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(50*cnt/total_s)

        if assignment_features:
            assignment_sink.addFeatures(assignment_features)

        # WRITE NODE LAYER
        node_features = []
        cnt = 0
        total_t = tlayer.featureCount()
        for tfeature in t_features.values():
            t_id = tfeature.attributes()[t_id_idx]
            attr = list(tfeature.attributes())
            for field in sfields:
                attr.append(values[(t_id, field)])

            f = QgsFeature(node_fields)
            f.setGeometry(tfeature.geometry())
            f.setAttributes(attr)
            node_features.append(f)
            cnt += 1

            if len(node_features) >= 200:
                node_sink.addFeatures(node_features)
                node_features = []

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(50+50*cnt/total_t)

        if node_features:
            node_sink.addFeatures(node_features)

        # SHOW PROGRESS
        info(feedback, "Source features", total_s)
        info(feedback, "Target features", total_t)
        nncnt = sum((1 for x in values if abs(values[x]) > 0))
        info(feedback, "Non-zero assignments", nncnt)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.ASSIGN_OUTPUT: assignment_id, self.OUTPUT_NODES: node_id}
