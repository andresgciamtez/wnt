"""Export an EPANET demand scenario file."""

from qgis.core import (QgsProcessing,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFileDestination)
from .base import WntProcessingAlgorithm
from .messages import finish, info, start

class ScnFromDemandsAlgorithm(WntProcessingAlgorithm):
    """
    Build an epanet scenary file from nodal demands.
    """

    # DEFINE CONSTANTS
    INPUT_NODES = 'INPUT_NODES'
    DEM_FIELD = 'DEM_FIELD'
    OUTPUT = 'OUTPUT'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ScnFromDemandsAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'scn_from_demand'

    def displayName(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return 'Scenario from node demands'

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
        return self.tr('''<p>Creates an EPANET demand scenario file.</p>
<ul>
<li>Each demand category must be stored in a field of the node layer.</li>
<li>EPANET patterns must use the same names as the selected demand fields.</li>
</ul>
<p>Import the generated file in EPANET using <b>File &gt; Import &gt; Scenario</b>.</p>
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
                self.DEM_FIELD,
                self.tr('Field containing demand'),
                'demand',
                self.INPUT_NODES,
                allowMultiple=True,
                optional=True
                )
            )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Epanet scenario file'),
                fileFilter='*.scn'
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodes = self.parameterAsSource(parameters, self.INPUT_NODES, context)
        defields = self.parameterAsFields(parameters, self.DEM_FIELD, context)

        # IF NO FIELD WAS SELECTED RETURN {}
        if not defields:
            return {}

        # WRITE FILE
        cnt = 0
        scnfn = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        with open(scnfn, 'w', encoding='utf-8') as file:
            file.write('; File generated automatically by Water Network Tools \n')
            file.write('[DEMANDS] \n')
            file.write(';Node    Demand    Pattern \n')
            feedback.setProgress(5) # Update the progress bar

            for f in nodes.getFeatures():
                for field in defields:
                    if f[field] and f['type'] == 'JUNCTION':
                        cnt += 1
                        line = '{}  {}  {} \n'.format(f['id'], f[field], field)
                        file.write(line)

        # SHOW INFO
        start(feedback, self.displayName())
        info(feedback, "Node demands", cnt)
        info(feedback, "Demand categories", len(defields))
        info(feedback, "Output file", scnfn)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: scnfn}

