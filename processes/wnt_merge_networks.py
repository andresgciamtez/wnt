"""Merge two network layer pairs."""

from qgis.core import (QgsFeature,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource
                       )
from .base import WntProcessingAlgorithm
from .messages import crs as log_crs
from .messages import error, finish, info, start, warning


def aligned_feature(feature, fields):
    """Return a copy of feature with attributes aligned to fields by name."""
    new_feature = QgsFeature(fields)
    new_feature.setGeometry(feature.geometry())
    attributes = []
    FIELDS_SOURCE = feature.fields()
    for field in fields:
        index = FIELDS_SOURCE.lookupField(field.name())
        attributes.append(feature.attributes()[index] if index >= 0 else None)
    new_feature.setAttributes(attributes)
    return new_feature

class MergeNetworksAlgorithm(WntProcessingAlgorithm):
    """
    Built a network from lines.
    """

    # DEFINE CONSTANTS
    INPUT_NODES_1 = 'INPUT_NODES_1'
    INPUT_LINES_1 = 'INPUT_LINES_1'
    INPUT_NODES_2 = 'INPUT_NODES_2'
    INPUT_LINES_2 = 'INPUT_LINES_2'
    OUTPUT_NODES = 'OUTPUT_NODES'
    OUTPUT_LINES = 'OUTPUT_LINES'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return MergeNetworksAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'merge_networks'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Merge networks'

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
        return self.tr('''<p>Merges two networks from their node and link layers.</p>
<ul>
<li>Connection nodes must share the same <code>id</code>.</li>
<li>The merge is created even when matching connection nodes are not coincident.</li>
<li>The maximum connection distance is reported in the log.</li>
</ul>
<p>Validate the merged network after running this algorithm.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NODES_1,
                self.tr('First node layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES_1,
                self.tr('First link layer input'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NODES_2,
                self.tr('Second node layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES_2,
                self.tr('Second link layer input'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )

        # ADD NODE AND LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('Merged node layer'),
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
                self.tr('Merged link layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        n1lay = self.parameterAsSource(parameters, self.INPUT_NODES_1, context)
        l1lay = self.parameterAsSource(parameters, self.INPUT_LINES_1, context)
        n2lay = self.parameterAsSource(parameters, self.INPUT_NODES_2, context)
        l2lay = self.parameterAsSource(parameters, self.INPUT_LINES_2, context)

        # CHECK CRS
        crs = n1lay.sourceCrs()
        if crs == l1lay.sourceCrs() == n2lay.sourceCrs() == l2lay.sourceCrs():

            # SEND INFORMATION TO THE USER
            start(feedback, self.displayName())
            log_crs(feedback, crs)
        else:
            error(feedback, "Layers have different CRS")
            return {}

        # GENERATE MERGED NODE LAYER
        node_fields = n1lay.fields()
        for field in n2lay.fields():
            if node_fields.lookupField(field.name()) < 0:
                node_fields.append(field)
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            node_fields,
            QgsWkbTypes.Point,
            crs
            )

        # GENERATE MERGED LINK LAYER
        link_fields = l1lay.fields()
        for field in l2lay.fields():
            if link_fields.lookupField(field.name()) < 0:
                link_fields.append(field)
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            link_fields,
            QgsWkbTypes.LineString,
            crs
            )

        # ADD FEATURES
        f = QgsFeature()
        g = QgsFeature()

        # CHECK DISTANCE
        dmax = 0
        ndmax = None

        # ADD NODES FROM FIRST NODE LAYER
        cnt = 0
        over = 0
        nofn = n1lay.featureCount()+n2lay.featureCount()
        nodes1 = set()
        for f in n1lay.getFeatures():
            cnt += 1
            nodes1.add(f['id'])
            node_sink.addFeature(aligned_feature(f, node_fields))

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(50*cnt/nofn)

        # ADD FROM SECOND NODE LAYER
        for f in n2lay.getFeatures():
            cnt += 1
            if not f['id'] in nodes1:
                node_sink.addFeature(aligned_feature(f, node_fields))
            else:

                # EXISTING NODE SO CHECK OVERLAPPING
                for g in n1lay.getFeatures():
                    if g['id'] == f['id']:
                        over += 1
                        dist = f.geometry().distance(g.geometry())
                        if dist > dmax:
                            dmax = dist
                            ndmax = f['id']

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(50*cnt/nofn)

        # SHOW DISTANCE MAX
        if dmax > 0:
            warning(feedback, f"Connection node {ndmax} distance is {dmax}")

        # ADD LINKS
        cnt = 0
        nofl = l1lay.featureCount()+l2lay.featureCount()
        for layer in [l1lay, l2lay]:
            for f in layer.getFeatures():
                cnt += 1
                link_sink.addFeature(aligned_feature(f, link_fields))

                # SHOW PROGRESS
                if cnt % 100 == 0:
                    feedback.setProgress(50+50*cnt/nofl)

        # SHOW INFO
        info(feedback, "Input nodes", nofn)
        info(feedback, "Input links", nofl)
        info(feedback, "Output nodes", nofn - over)
        info(feedback, "Output links", nofl)
        info(feedback, "Connection nodes", over)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_NODES: node_id, self.OUTPUT_LINES: link_id}

