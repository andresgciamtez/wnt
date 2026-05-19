"""Set node elevations from a raster DEM."""

from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField
                      )
from .base import WntProcessingAlgorithm
from .messages import crs as log_crs
from .messages import error, finish, info, start

class ElevationFromRasterAlgorithm(WntProcessingAlgorithm):
    """
    Set the node elevation from a DEM in raster format.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    INPUT_DEM = 'INPUT_DEM'
    FIELD_ELEVATION = 'FIELD_ELEVATION'
    OUTPUT = 'OUTPUT'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ElevationFromRasterAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'elevation_from_raster'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Node elevation from DEM'

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
        return self.tr('''<p>Sets node elevations from a raster DEM.</p>
<ul>
<li>Reads elevation values from the DEM at each node position.</li>
<li>Writes the values to the selected elevation field.</li>
<li>Nodes outside the raster extent are reported as skipped.</li>
</ul>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT SOURCES
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_NODES,
                self.tr('Node vector layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_ELEVATION,
                self.tr('Elevation field.'),
                None,
                self.INPUT_NODES
                )
            )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM,
                self.tr('DEM raster layer input')
                )
            )

        #ADD THE OUTPUT SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Nodes with elevation layer'),
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodelayer = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        demlayer = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        efield = self.parameterAsString(parameters, self.FIELD_ELEVATION, context)

        # CHECK CRS
        crs = nodelayer.sourceCrs()
        if crs == demlayer.crs():

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
            nodelayer.fields(),
            nodelayer.wkbType(),
            nodelayer.sourceCrs()
            )

        # MAIN LOOP READ/WRITE POINTS
        pcnt = 0
        scnt = 0

        for feat in nodelayer.getFeatures():
            val, res = demlayer.dataProvider().sample(feat.geometry().asPoint(), 1)
            if res:
                pcnt += 1
                feat[efield] = val
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
            else:
                scnt += 1

            # SHOW PROGRESS
            if (pcnt+scnt) % 100 == 0:
                feedback.setProgress(100*(pcnt+scnt)/nodelayer.featureCount())
        info(feedback, "Processed nodes", pcnt)
        info(feedback, "Skipped nodes", scnt)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: dest_id}

