# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFileDestination)
import processing

class DiameterAndRoughness(QgsProcessingAlgorithm):
    """
    Create a epanet scenary file with diameter and roughness
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    LINKS_INPUT = 'LINKS_INPUT'
    D_FIELD_INPUT = 'D_FIELD_INPUT'
    R_FIELD_INPUT = 'R_FIELD_INPUT'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DiameterAndRoughness()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'pipe_property_scenario'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Pipe property scenario')

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Net tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'nettools'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Make an epanet scenario file with diameter and roughness")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # Adding the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINKS_INPUT,
                self.tr('Input links layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.D_FIELD_INPUT,
                self.tr('Field containing diameter'),
                'diameter',
                self.LINKS_INPUT
            )
        )
        self.addParameter(
            QgsProcessingParameterField (
                self.R_FIELD_INPUT,
                self.tr('Field containing roughness'),
                'roughness',
                self.LINKS_INPUT
            )
        )
        # Adding a feature sink in which to store our processed results.
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Epanet scenario file'),
                fileFilter='*.scn'
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # INPUT        
        linksinput = self.parameterAsSource(parameters, self.LINKS_INPUT, context)
        dfield = self.parameterAsString(parameters, self.D_FIELD_INPUT, context)
        rfield = self.parameterAsString(parameters, self.R_FIELD_INPUT, context)
        
        # OUTPUT
        scnfn = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        f = open(scnfn, 'w')
        
        f.write('; File generated automatically by nettools.py \n')
        f.write('[DIAMETERS] \n')
        f.write(';Pipe    Diameter \n')
        for feature in linksinput.getFeatures():
            f.write('{}    {} \n'.format(feature['id'],feature[dfield]))
        
        f.write(' \n')
        f.write('[ROUGHNESS] \n')
        f.write(';Pipe    Roughness \n')
        for feature in linksinput.getFeatures():
            f.write('{}    {} \n'.format(feature['id'],feature[rfield]))
        
        f.close()

        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {'OUTPUT': scnfn}
