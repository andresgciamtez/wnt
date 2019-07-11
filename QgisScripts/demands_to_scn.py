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

class DemandScenario(QgsProcessingAlgorithm):
    """
    Create a epanet scenary file with diameter and roughness
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    NODES_INPUT = 'NODES_INPUT'
    DE_FIELD_INPUT = 'DE_FIELD_INPUT'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return DemandScenario()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'nodal_demand_scenario'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
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
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Make an epanet scenario file with nodal demands.")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # Adding the input vector features source.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODES_INPUT,
                self.tr('Input nodes layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        # Adding fields with demand.
        self.addParameter(
            QgsProcessingParameterField(
                self.DE_FIELD_INPUT,
                self.tr('Fields containing demand'),
                'demand',
                self.NODES_INPUT,
                allowMultiple = True,
                optional = True
            )
        )
        # Adding a file destination.
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
        nodesinput = self.parameterAsSource(parameters, self.NODES_INPUT, context)
        dfields = self.parameterAsFields(parameters, self.DE_FIELD_INPUT, context)
        
        # IF NO FIELD WAS SELECTED RETURN {}  
        if len(dfields) == 0:
            return {}
        
        # OUTPUT
        scnfn = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        file = open(scnfn, 'w')
        
        file.write('; File generated automatically by nettools.py \n')
        file.write('[DEMANDS] \n')
        file.write(';Node    Demand    Pattern \n')
        for feat in nodesinput.getFeatures():
            for field in dfields:
                if feat[field] != None and feat['type'] == 'JUNCTION':
                    line ='{}  {}  {} \n'.format(feat['id'],feat[field], field)
                    file.write(line)
        
        file.close()

        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {'OUTPUT': scnfn}
