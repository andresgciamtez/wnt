"""Configure the EPANET toolkit library path."""

from qgis.core import (
                       QgsProcessingParameterFile
                       )
from .base import WntProcessingAlgorithm
from .messages import error, finish, info, start
from ..utils.utils_epanet_api import (
    EpanetConfigurationError,
    EpanetError,
    EpanetToolkit,
    toolkit_config_path,
    write_toolkit_library_path,
)

class ConfigToolkitAlgorithm(WntProcessingAlgorithm):
    """
    Set EPANET lib path in tookit.ini file.
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
        return 'Configure EPANET lib'

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Import')

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
                self.tr('EPANET lib')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        lib_file = self.parameterAsFile(parameters, self.INPUT, context)
        start(feedback, self.displayName())

        # CHECK TOOLKIT
        try:
            toolkit = EpanetToolkit.from_library_path(lib_file)
            toolkit.check_available()
            toolkit_info = toolkit.info()
        except EpanetConfigurationError as exc:
            error(feedback, str(exc))
            return {}
        except EpanetError as exc:
            error(feedback, exc.message)
            return {}

        # OUTPUT
        init_file = write_toolkit_library_path(lib_file, toolkit_config_path())

        # SHOW INFO
        info(feedback, "Configuration file", init_file)
        info(feedback, "EPANET toolkit library", lib_file)
        info(feedback, "Platform", f"{toolkit_info.platform} {toolkit_info.architecture}")
        info(feedback, "EPANET toolkit version", toolkit_info.version)
        info(feedback, "EPANET toolkit API", toolkit_info.api)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {}

