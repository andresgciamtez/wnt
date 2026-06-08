"""Set node elevations from LandXML TIN surfaces."""

from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingParameterEnum,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString
                      )
from .base import (OUTPUT_MODE_NEW, OUTPUT_MODE_UPDATE, OUTPUT_MODE_OPTIONS,
                   WntProcessingAlgorithm, field_index, missing_fields,
                   set_progress, update_layer_attributes)
from .widgets import LandXmlSurfaceWidgetWrapper
from ..utils.utils_tin import TIN
from .messages import crs as log_crs
from .messages import error, finish, info, start

class ElevationFromTINAlgorithm(WntProcessingAlgorithm):
    """
    Set the node elevation from a TIN surface in LandXML format.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    FIELD_ELEVATION = 'FIELD_ELEVATION'
    INPUT_TIN = 'INPUT_TIN'
    SURFACE_NAME = 'SURFACE_NAME'
    SURFACE_NAMES = 'SURFACE_NAMES'
    OUTPUT_MODE = 'OUTPUT_MODE'
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
        return self.tr('''<p>Sets node elevations from one LandXML TIN surface.</p>
<ul>
<li>If no surface is selected, the first TIN surface found in the file is used and reported.</li>
<li>The selected surface is loaded once and searched with its spatial index.</li>
<li>Can create a new output layer or update the input node layer.</li>
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
        surface_parameter = QgsProcessingParameterString(
            self.SURFACE_NAME,
            self.tr('Surface name'),
            defaultValue='',
            multiLine=False,
            optional=True
            )
        surface_parameter.setMetadata({
            'widget_wrapper': {'class': LandXmlSurfaceWidgetWrapper},
            'landxml_file_parameter': self.INPUT_TIN,
        })
        self.addParameter(
            surface_parameter
            )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OUTPUT_MODE,
                self.tr('Output mode'),
                options=[self.tr(option) for option in OUTPUT_MODE_OPTIONS],
                defaultValue=OUTPUT_MODE_NEW,
                optional=False
                )
            )

        #ADD THE OUTPUT SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Nodes with elevation layer'),
                optional=True
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        output_mode = self.parameterAsEnum(parameters, self.OUTPUT_MODE, context)
        if output_mode == OUTPUT_MODE_UPDATE:
            nodelayer = self.parameterAsVectorLayer(parameters, self.INPUT_NODES, context)
        else:
            nodelayer = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        efield = self.parameterAsString(parameters, self.FIELD_ELEVATION, context)
        tinlayer = self.parameterAsFile(parameters, self.INPUT_TIN, context)
        selected_surface_name = self.parameterAsString(parameters, self.SURFACE_NAME, context).strip()
        if not selected_surface_name and self.SURFACE_NAMES in parameters:
            selected_surface_name = str(parameters.get(self.SURFACE_NAMES) or '').strip()

        missing = missing_fields(nodelayer, [efield])
        if nodelayer.fields().names() and missing:
            error(feedback, "Node layer is missing required fields: " + ", ".join(missing))
            return {}

        using_default_surface = not selected_surface_name

        # SEND INFORMATION TO THE USER
        crs = nodelayer.sourceCrs()
        start(feedback, self.displayName())
        log_crs(feedback, crs)

        if output_mode == OUTPUT_MODE_NEW:
            # OUTPUT
            (sink, dest_id) = self.parameterAsSink(
                parameters,
                self.OUTPUT,
                context,
                nodelayer.fields(),
                nodelayer.wkbType(),
                nodelayer.sourceCrs()
                )
        else:
            sink = None
            dest_id = getattr(nodelayer, 'id', lambda: self.INPUT_NODES)()

        nodes = list(nodelayer.getFeatures())
        points = [feature.geometry().asPoint() for feature in nodes]
        point_tuples = [(point.x(), point.y()) for point in points]
        try:
            surface = TIN()
            surface.from_landxml(tinlayer, selected_surface_name)
            surface_elevations = surface.elevations(point_tuples)
        except Exception as exc:
            error(feedback, str(exc))
            return {}

        # SHOW PROGRESS
        info(feedback, "Input nodes", len(points))
        info(feedback, "LandXML surface selected", surface.surface_name)
        if using_default_surface:
            info(feedback, "Default LandXML surface used", surface.surface_name)
        feedback.setProgress(50)

        result_elevations = []
        skipped = 0
        for value in surface_elevations:
            if value is None:
                result_elevations.append(None)
                skipped += 1
                continue
            result_elevations.append(value)

        elevation_index = field_index(nodelayer.fields(), efield)
        updates = {}
        for count, (feature, z) in enumerate(zip(nodes, result_elevations), start=1):
            if feedback.isCanceled():
                return {}
            if output_mode == OUTPUT_MODE_UPDATE:
                updates[feature.id()] = {elevation_index: z}
            else:
                feature[efield] = z
                sink.addFeature(feature, QgsFeatureSink.FastInsert)
            set_progress(feedback, 50, 100, count, len(nodes))

        if output_mode == OUTPUT_MODE_UPDATE:
            try:
                update_layer_attributes(nodelayer, updates)
            except RuntimeError as exc:
                error(feedback, str(exc))
                return {}

        # SHOW PROGRESS
        info(feedback, "Skipped nodes", skipped)
        info(feedback, "Output mode", OUTPUT_MODE_OPTIONS[output_mode])
        finish(feedback)

        # OUTPUT
        return {self.OUTPUT: dest_id}
