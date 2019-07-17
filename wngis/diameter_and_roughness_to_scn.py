# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFileDestination)

class DiameterAndRoughness(QgsProcessingAlgorithm):
    """
    Build an epanet scenary file from pipe diameter and roughness.
    """

    # DEFINE CONSTANTS

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
        """
        Create a instance and return a new copy of algorithm.
        """
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
        Returns a localised short helper string for the algorithm.
        """
        return self.tr("Make an epanet scenario file with pipe diameter and roughness.")

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """
        
        # ADD THE INPUT
        
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
        
        
        # ADD A FILE DESTINATION
        
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
        
        links = self.parameterAsSource(parameters, self.LINKS_INPUT, context)
        dfield = self.parameterAsString(parameters, self.D_FIELD_INPUT, context)
        rfield = self.parameterAsString(parameters, self.R_FIELD_INPUT, context)
        
        # OUTPUT
        
        scnfile = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        
        # WRITE FILE
        
        cnt = 0
        file = open(scnfile, 'w')
        file.write('; File generated automatically by nettools.py \n')
        file.write('[DIAMETERS] \n')
        file.write(';Pipe    Diameter \n')
        
        
        for feature in links.getFeatures():
            if feature['type'] in ['PIPE', 'CVPIPE']:
                cnt += 1    
                file.write('{}    {} \n'.format(feature['id'],feature[dfield]))
 
        file.write(' \n')
        file.write('[ROUGHNESS] \n')
        file.write(';Pipe    Roughness \n')
        
        for feature in links.getFeatures():
            if feature['type'] in ['PIPE', 'CVPIPE']:
                file.write('{}    {} \n'.format(feature['id'],feature[rfield]))
        
        file.close()
        
        msg = 'Pipe diameter and roughness add: {}.'.format(cnt)
        feedback.pushInfo(msg)

        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {self.OUTPUT: scnfile}
