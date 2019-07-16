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

class DemandScenario(QgsProcessingAlgorithm):
    """
    Build an epanet scenary file with diameter and roughness.
    """

    # DEFINE CONSTANTS

    NODES_INPUT = 'NODES_INPUT'
    DE_FIELD_INPUT = 'DE_FIELD_INPUT'
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
        return DemandScenario()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'nodal_demand_scenario'

    def displayName(self):
        """
        Returns a localised short helper string for the algorithm
        """
        return self.tr('Nodal demand scenario')

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
        return self.tr("Make an epanet scenario file with nodal demands.")

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """
        
        # ADD THE INPUT SOURCES
        
        # Adding the input vector features source
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODES_INPUT,
                self.tr('Input nodes layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        # Adding fields with demand
        self.addParameter(
            QgsProcessingParameterField(
                self.DE_FIELD_INPUT,
                self.tr('Field containing demand'),
                'demand',
                self.NODES_INPUT,
                allowMultiple = True,
                optional = True
            )
        )
        # Adding a file destination
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
        
        input = self.parameterAsSource(parameters, self.NODES_INPUT, context)
        defields = self.parameterAsFields(parameters, self.DE_FIELD_INPUT, context)
        
        # OUTPUT
        
        scnfn = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        file = open(scnfn, 'w')
        
        
        # IF NO FIELD WAS SELECTED RETURN {}  
        if len(defields) == 0:
            return {}
        
        # WRITE FILE
        
        cnt = 0
        scnfn = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        file = open(scnfn, 'w')
        file.write('; File generated automatically by nettools.py \n')
        file.write('[DEMANDS] \n')
        file.write(';Node    Demand    Pattern \n')
        feedback.setProgress(5) # Update the progress bar
        
        for feat in input.getFeatures():
            for field in defields:
                if feat[field] != None and feat['type'] == 'JUNCTION':
                    cnt += 1
                    line ='{}  {}  {} \n'.format(feat['id'],feat[field], field)
                    file.write(line)
        
        file.close()
        
        msg = 'Node demands add: {},  types: {}.'.format(cnt, len(defields))
        feedback.pushInfo(msg)

        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {self.OUTPUT: scnfn}
