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
                   parse_name_list, set_progress, update_layer_attributes)
from ..utils.utils_tin import ACCEPTABLE_DEVIATION, TIN, surface_names
from .messages import crs as log_crs
from .messages import error, finish, info, start

class ElevationFromTINAlgorithm(WntProcessingAlgorithm):
    """
    Set the node elevation from one or more TIN surfaces in LandXML format.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    FIELD_ELEVATION = 'FIELD_ELEVATION'
    INPUT_TIN = 'INPUT_TIN'
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
        return self.tr('''<p>Sets node elevations from one or more LandXML TIN surfaces.</p>
<ul>
<li>Surface names are written as a comma or semicolon separated list.</li>
<li>If no surface is selected, the first TIN surface found in the file is used and reported.</li>
<li>When several selected surfaces cover the same node, elevations must be consistent.</li>
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
        self.addParameter(
            QgsProcessingParameterString(
                self.SURFACE_NAMES,
                self.tr('Surface names'),
                defaultValue='',
                multiLine=False,
                optional=True
                )
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
        selected_surface_names = parse_name_list(self.parameterAsString(parameters, self.SURFACE_NAMES, context))

        missing = missing_fields(nodelayer, [efield])
        if nodelayer.fields().names() and missing:
            error(feedback, "Node layer is missing required fields: " + ", ".join(missing))
            return {}

        try:
            available_surfaces = surface_names(tinlayer)
        except Exception as exc:
            error(feedback, str(exc))
            return {}
        if not available_surfaces:
            error(feedback, "No LandXML TIN surfaces found")
            return {}

        if selected_surface_names:
            missing_surfaces = [name for name in selected_surface_names if name not in available_surfaces]
            if missing_surfaces:
                error(feedback, "LandXML TIN surfaces not found: " + ", ".join(missing_surfaces))
                return {}
            names_to_load = selected_surface_names
            using_default_surface = False
        else:
            names_to_load = [available_surfaces[0]]
            using_default_surface = True

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
        elevations_by_surface = []
        try:
            for name in names_to_load:
                surface = TIN()
                surface.from_landxml(tinlayer, name)
                elevations_by_surface.append((surface.surface_name, surface.elevations(point_tuples)))
        except Exception as exc:
            error(feedback, str(exc))
            return {}

        # SHOW PROGRESS
        info(feedback, "Input nodes", len(points))
        info(feedback, "LandXML surfaces selected", ", ".join(name for name, _ in elevations_by_surface))
        if using_default_surface:
            info(feedback, "Default LandXML surface used", elevations_by_surface[0][0])
        feedback.setProgress(50)

        result_elevations = []
        skipped = 0
        for index, feature in enumerate(nodes):
            values = [
                (name, values[index])
                for name, values in elevations_by_surface
                if values[index] is not None
            ]
            if not values:
                result_elevations.append(None)
                skipped += 1
                continue
            reference_name, reference_value = values[0]
            conflicts = [
                (name, value)
                for name, value in values[1:]
                if abs(value - reference_value) > ACCEPTABLE_DEVIATION
            ]
            if conflicts:
                node_id = feature['id'] if 'id' in feature.fields().names() else str(index + 1)
                conflict_text = ["{}={}".format(reference_name, reference_value)]
                conflict_text.extend("{}={}".format(name, value) for name, value in conflicts)
                error(feedback, "Conflicting TIN elevations for node {}: {}".format(node_id, ", ".join(conflict_text)))
                return {}
            result_elevations.append(reference_value)

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
