"""Configure the EPANET toolkit library path."""

import configparser
from pathlib import Path
from qgis.core import (
                       QgsProcessingParameterFile
                       )
from .base import WntProcessingAlgorithm
from .messages import finish, info, start

class ConfigToolkitAlgorithm(WntProcessingAlgorithm):
    """
    Set epanet lib path in tookit.ini file.
    """

    # DEFINE CONSTANTS
    INPUT = 'INPUT'


    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ConfigToolkitAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'config_toolkit'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return 'Configure epanet lib'

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return 'Import'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'import'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''<p>Sets the path to the EPANET toolkit library.</p>
<ul>
<li>The path is stored in <code>toolkit.ini</code>.</li>
<li>Configure this before importing EPANET simulation results.</li>
</ul>
<p>EPANET toolkit libraries can be obtained from the EPA EPANET download page or from a compatible EPANET toolkit build.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """
        # ADD A FILE DESTINATION
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Epanet lib')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # OUTPUT
        lib_file = self.parameterAsFile(parameters, self.INPUT, context)
        init_file = Path(__file__).resolve().parents[1] / 'toolkit.ini'
        start(feedback, self.displayName())
        config = configparser.ConfigParser()
        config.read(init_file)
        if not config.has_section('EPANET'):
            config.add_section('EPANET')
        config['EPANET']['lib'] = lib_file
        with open(init_file, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

        # SHOW INFO
        info(feedback, "Configuration file", init_file)
        info(feedback, "EPANET toolkit library", lib_file)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {}

