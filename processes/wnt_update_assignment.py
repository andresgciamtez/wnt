"""Update demand assignments after editing connection lines."""

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsWkbTypes
                       )
from .base import WntProcessingAlgorithm
from .messages import crs as log_crs
from .messages import error, finish, info, message, start

POS_TOLERANCE = 1e-4

class UpdateAssignmentAlgorithm(WntProcessingAlgorithm):
    """
    Update demands.
    """

    # DEFINE CONSTANTS
    SOURCE_INPUT = 'SOURCE_LAYER_INPUT'
    TARGET_INPUT = 'TARGET_LAYER_INPUT'
    ASSIGN_INPUT = 'ASSIGNMENT_LAYER_INPUT'
    TARGET_OUTPUT = 'TARGET_LAYER_OUTPUT'
    ASSIGN_OUTPUT = 'ASSIGNMENT_LAYER_OUTPUT'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return UpdateAssignmentAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'update_assignment'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Update assignment'

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
        return self.tr('''<p>Updates demand assignments after editing assignment lines.</p>
<ul>
<li>Recalculates demand values in the target node layer.</li>
<li>Only the target endpoint of an assignment line can be moved.</li>
<li>The source endpoint must remain on the original source feature.</li>
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
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET_INPUT,
                self.tr('Target layer'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ASSIGN_INPUT,
                self.tr('Edited assignment layer'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )

        # ADD FEATURE SINKS
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.TARGET_OUTPUT,
                self.tr('Updated target layer')
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ASSIGN_OUTPUT,
                self.tr('Updated assignment layer')
                )
            )


    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        slayer = self.parameterAsSource(parameters, self.SOURCE_INPUT, context)
        tlayer = self.parameterAsSource(parameters, self.TARGET_INPUT, context)
        alayer = self.parameterAsSource(parameters, self.ASSIGN_INPUT, context)

        # CHECK CRS
        crs = slayer.sourceCrs()
        if crs == tlayer.sourceCrs() == alayer.sourceCrs():

            # SEND INFORMATION TO THE USER
            start(feedback, self.displayName())
            log_crs(feedback, crs)
        else:
            error(feedback, "Layers have different CRS")
            return {}

        # OUTPUT LAYERS
        (assign_sink, assign_id) = self.parameterAsSink(
            parameters,
            self.ASSIGN_OUTPUT,
            context,
            alayer.fields(),
            QgsWkbTypes.LineString,
            crs
            )
        (target_sink, target_id) = self.parameterAsSink(
            parameters,
            self.TARGET_OUTPUT,
            context,
            tlayer.fields(),
            QgsWkbTypes.Point,
            crs
            )

        # CHECK SOURCE POSITION AND READ SOURCE VALUES
        field_names = alayer.fields().names()
        field_names.remove("source")
        field_names.remove("target")
        src_pos = {}
        src_fds = {}
        assignments = []
        for f in slayer.getFeatures():
            src_pos[f["id"]] = f.geometry().asPoint()
            for name in field_names:
                src_fds[(f["id"], name)] = f[name]
        for f in alayer.getFeatures():
            start_point = f.geometry().asPolyline()[0]
            if start_point.distance(src_pos[f["source"]]) > POS_TOLERANCE:
                msg = f'Source point misplaced: {f["source"]}'
                error(feedback, msg)
                return {}
            for name in field_names:
                f[name] = src_fds[(f["source"], name)]
            assignments.append(f)

        # SHOW PROGRESS
        message(feedback, "All sources are placed correctly")
        feedback.setProgress(50)

        # UPDATE TARGET IDS AND RECOMPUTE
        tar_pos = {}
        values = {}
        cnt = 0
        for f in tlayer.getFeatures():
            tar_pos[f["id"]] = f.geometry().asPoint()
            for name in field_names:
                values[(f["id"], name)] = 0
        for f in assignments:
            end_point = f.geometry().asPolyline()[-1]
            if end_point.distance(tar_pos[f["target"]]) > POS_TOLERANCE:
                for id_, point in tar_pos.items():
                    if end_point.distance(point) <= POS_TOLERANCE:
                        msg = f'Updated position of target from: {f["target"]}'
                        msg += f' to: {id_}'
                        f["target"] = id_
                        cnt += 1
                        message(feedback, msg)
                        break
                else:
                    msg = f'Misassignment. Source: {f["source"]}'
                    msg += f' target: {f["target"]}'
                    error(feedback, msg)
                    return {}
            for name in field_names:
                values[(f["target"], name)] += f[name]
        info(feedback, "Updated targets", cnt)
        # WRITE ASSIGNEMENT LAYER
        for f in assignments:
            assign_sink.addFeature(f)

        # WRITE TARGET LAYER
        for f in tlayer.getFeatures():
            for name in field_names:
                f[name] = values[f['id'], name]
            target_sink.addFeature(f)

        # SHOW PROGRESS
        feedback.setProgress(100)

        # SHOW PROGRESS
        info(feedback, "Source features", slayer.featureCount())
        info(feedback, "Target features", tlayer.featureCount())
        info(feedback, "Assignment features", alayer.featureCount())
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.ASSIGN_OUTPUT: assign_id, self.TARGET_OUTPUT: target_id}

