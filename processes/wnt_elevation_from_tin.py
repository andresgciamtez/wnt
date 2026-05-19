"""Set node elevations from a LandXML TIN surface."""

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString
                      )
from .base import WntProcessingAlgorithm
from ..utils.tin import TIN
from .messages import crs as log_crs
from .messages import finish, info, start

class ElevationFromTINAlgorithm(WntProcessingAlgorithm):
    """
    Set the node elevation from a TIN in LandXML format.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    FIELD_ELEVATION = 'FIELD_ELEVATION'
    INPUT_TIN = 'INPUT_TIN'
    SURFACE_NAME = 'SURFACE_NAME'
    OUTPUT = 'OUTPUT'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ElevationFromTINAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'elevation_from_tin'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return 'Node elevation from TIN (LandXML)'

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
        return self.tr('''<p>Sets node elevations from a LandXML TIN surface.</p>
<ul>
<li>Reads the selected LandXML surface, or the first surface when no name is provided.</li>
<li>Interpolates elevations at node positions.</li>
<li>Writes the values to the selected elevation field.</li>
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
                self.tr('Elevation field'),
                'elevation',
                self.INPUT_NODES
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT_TIN,
                self.tr('LandXML file'),
                extension='xml'
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.SURFACE_NAME,
                self.tr('Surface name (if empty, first found)'),
                defaultValue='',
                multiLine=False,
                optional=True
                )
            )

        #ADD THE OUTPUT SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Nodes with elevation layer')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodelayer = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        efield = self.parameterAsString(parameters, self.FIELD_ELEVATION, context)
        tinlayer = self.parameterAsFile(parameters, self.INPUT_TIN, context)
        sname = self.parameterAsString(parameters, self.SURFACE_NAME, context)

        # SEND INFORMATION TO THE USER
        crs = nodelayer.sourceCrs()
        start(feedback, self.displayName())
        log_crs(feedback, crs)

        # OUTPUT
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            nodelayer.fields(),
            nodelayer.wkbType(),
            nodelayer.sourceCrs()
            )

        # READ NODES
        points = []
        cnt = 0

        for f in  nodelayer.getFeatures():
            point = f.geometry().asPoint().x(), f.geometry().asPoint().y()
            points.append(point)
        surface = TIN()
        surface.from_landxml(tinlayer, sname)
        elevations = surface.elevations(points)

        # SHOW PROGRESS
        info(feedback, "Input nodes", len(points))
        feedback.setProgress(50)

        # WRITE NODES
        for f, z in zip(nodelayer.getFeatures(), elevations):
            f[efield] = z
            sink.addFeature(f) # , QgsFeatureSink.FastInsert)
            if z is None:
                cnt += 1

        # SHOW PROGRESS
        feedback.setProgress(100)
        info(feedback, "Skipped nodes", cnt)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: dest_id}
