"""Export an EPANET pipe properties scenario file."""

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFileDestination)
from .base import WntProcessingAlgorithm
from .messages import finish, info, start

class PipePropiertiesToEpanetScenarioAlgorithm(WntProcessingAlgorithm):
    """
    Build an EPANET scenary file from pipe diameter and roughness.
    """

    # DEFINE CONSTANTS

    INPUT_LINES = 'INPUT_LINES'
    FIELD_DIAMETER = 'FIELD_DIAMETER'
    FIELD_ROUGHNESS = 'FIELD_ROUGHNESS'
    OUTPUT = 'OUTPUT'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return PipePropiertiesToEpanetScenarioAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'network_to_epanet_pipe_propierties_scenario'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Pipe propierties to epanet scenario file (.scn)'

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
        return self.tr('''<p>Creates an EPANET <code>.scn</code> scenario file with pipe diameters and roughness values.</p>
<ul>
<li>Diameters are read from the selected mandatory diameter field.</li>
<li>Roughness values are read from the selected mandatory roughness field.</li>
</ul>
<p>Import the generated file in EPANET using <b>File &gt; Import &gt; Scenario</b>.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_LINES,
                self.tr('Input link layer'),
                [QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_DIAMETER,
                self.tr('Diameter field'),
                'diameter',
                self.INPUT_LINES
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.FIELD_ROUGHNESS,
                self.tr('Roughness field'),
                'roughness',
                self.INPUT_LINES
                )
            )

        # ADD A FILE DESTINATION
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('EPANET scenario file'),
                fileFilter='*.scn'
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        links = self.parameterAsSource(parameters, self.INPUT_LINES, context)
        dfield = self.parameterAsString(parameters, self.FIELD_DIAMETER, context)
        rfield = self.parameterAsString(parameters, self.FIELD_ROUGHNESS, context)

        # OUTPUT
        scnfile = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        # WRITE FILE
        cnt = 0
        pipe_features = [
            feature for feature in links.getFeatures()
            if str(feature['type'] or '').upper() in ['PIPE', 'CVPIPE']
        ]
        with open(scnfile, 'w', encoding='utf-8') as file:
            file.write('; File generated automatically by Water Network Tools \n')
            file.write('[DIAMETERS] \n')
            file.write(';Pipe    Diameter \n')

            for feature in pipe_features:
                cnt += 1
                file.write('{}    {} \n'.format(feature['id'], feature[dfield]))

            file.write(' \n')
            file.write('[ROUGHNESS] \n')
            file.write(';Pipe    Roughness \n')

            for feature in pipe_features:
                file.write('{}    {} \n'.format(feature['id'], feature[rfield]))

        # SHOW INFO
        start(feedback, self.displayName())
        info(feedback, "Pipes written", cnt)
        info(feedback, "Output file", scnfile)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: scnfile}
