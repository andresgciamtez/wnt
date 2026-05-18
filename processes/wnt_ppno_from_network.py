"""Export PPNO sizing input from network layers."""

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from .base import WntProcessingAlgorithm
from ..utils import parser
from .messages import error, finish, info, start

class PpnoFromNetworkAlgorithm(WntProcessingAlgorithm):
    """
    Build a ppno data file (.ext) from node and link data.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    PRESS_FIELD = 'PRESS_FIELD'
    INPUT_LINES = 'INPUT_LINES'
    SERIES_FIELD = 'SERIES_FIELD'
    EPANET = 'EPANET'
    TEMPLATE = 'TEMPLATE'
    OUTPUT = 'OUTPUT'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return PpnoFromNetworkAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'ppno_from_network'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'ppno data file from network'

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return 'Export'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'export'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''<p>Creates a PPNO <code>.ext</code> data file for pipe sizing.</p>
<ul>
<li>The required pressure must be stored in a node layer field.</li>
<li>The pipe series must be stored in a link layer field.</li>
<li>The EPANET <code>.inp</code> file must contain the model to optimize.</li>
<li>The PPNO template must contain the available pipe series.</li>
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
                self.tr('Input node layer'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.PRESS_FIELD,
                self.tr('Required pressure field'),
                'Required pressure',
                self.INPUT_NODES,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
                self.tr('Input link layer'),
                [QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.SERIES_FIELD,
                self.tr('Pipe series field'),
                'Pipe series',
                self.INPUT_LINES,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.EPANET,
                self.tr('Epanet file'),
                extension='inp'
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.TEMPLATE,
                self.tr('ppno template file'),
                extension='ext'
                )
            )

        # ADD A FILE DESTINATION FOR RESULTS
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output ppno file'),
                fileFilter='*.ext'
                )
            )
    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodes = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        pfield = self.parameterAsFields(parameters, self.PRESS_FIELD, context)
        pfield = pfield[0]
        links = self.parameterAsSource(parameters, self.INPUT_LINES, context)
        sfield = self.parameterAsFields(parameters, self.SERIES_FIELD, context)
        sfield = sfield[0]
        epanet = self.parameterAsFile(parameters, self.EPANET, context)
        template = self.parameterAsFile(parameters, self.TEMPLATE, context)

        # OUTPUT
        extfile = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # CHECK CRS
        if nodes.sourceCrs() != links.sourceCrs():
            error(feedback, "Layers have different CRS")
            return {}

        # TEMPLATE
        ppnof = parser.SectionedText()
        ppnof.read(template)

        # TITLE SECTION
        msg = '; File generated automatically by Water Network Tools \n'
        ppnof.sections['TITLE'].append(msg)

        # INP SECTION
        ppnof.sections['INP'] = [epanet]

        # PRESSURES SECTION
        ncnt = 0
        for feature in nodes.getFeatures():
            if feature[pfield]:
                ncnt += 1
                line = feature['id']+' '*4 + str(feature[pfield])
                ppnof.sections['PRESSURES'].append(line)

        # PIPES SECTION
        pcnt = 0
        for feature in links.getFeatures():
            if feature[sfield]:
                pcnt += 1
                line = (feature['id']+' '*4 + str(feature[sfield]))
                ppnof.sections['PIPES'].append(line)

        # WRITE EXT FILE
        ppnof.write(extfile)

        # SHOW INFO
        start(feedback, self.displayName())
        info(feedback, "Nodes with minimum pressure", ncnt)
        info(feedback, "Pipes to size", pcnt)
        info(feedback, "Output file", extfile)
        finish(feedback)
        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: extfile}
