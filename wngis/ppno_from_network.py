# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingParameterEnum,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from htxt import Htxtf

class PpnoFromNetwork(QgsProcessingAlgorithm):
    """
    Build a ppno data file (.ext) from node and link data.
    """

    # DEFINE CONSTANTS

    NODES_INPUT = 'NODES_INPUT'
    P_FIELD_INPUT = 'P_FIELD_INPUT'
    LINKS_INPUT = 'LINKS_INPUT'
    S_FIELD_INPUT = 'S_FIELD_INPUT'
    EPANET_INPUT = 'EPANET_INPUT'
    ALGO_INPUT = 'ALGO_INPUT'
    TMPL_INPUT = 'TMPL_INPUT'
    OUTPUT = 'OUTPUT'
    ALGORITHMS = ['GD','DE','DA','NSGA2']
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return PpnoFromNetwork()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'Ppno_from_network'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('ppno from network')

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
        msg = "Make a ppno ext file from nodes and links. \n"
        msg += "In the node layer must be defined the pressure required. \n"
        msg += "In the link layer must be defined the pipe series. \n"
        msg += "Select the optimization algorithm, among: \n"
        msg += "GD, DE, DA or NSGA-II \n"
        msg += "The template must contain the catalog of pipe series."
        return self.tr(msg)

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT SOURCES
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODES_INPUT,
                self.tr('Input nodes layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.P_FIELD_INPUT,
                self.tr('Field containing required pressure'),
                'Required pressure',
                self.NODES_INPUT,
                allowMultiple = False,
                optional = False
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINKS_INPUT,
                self.tr('Input links layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.S_FIELD_INPUT,
                self.tr('Field containing pipe series'),
                'Pipe series',
                self.LINKS_INPUT,
                allowMultiple = False,
                optional = False
            )
        )
        self.addParameter(
            QgsProcessingParameterFile(
                self.EPANET_INPUT,
                self.tr('Epanet file (.inp)'),
                extension = 'inp'
            )
        )      
        self.addParameter(
            QgsProcessingParameterFile(
                self.TMPL_INPUT,
                self.tr('ppnp template file (.ext)'),
                extension = 'ext'
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ALGO_INPUT,
                self.tr('Algoritm'),
                options = self.ALGORITHMS,
                defaultValue = 0
            )
        )
            
        # ADD A FILE DESTINATION FOR RESULTS
           
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output ppno data file'),
                fileFilter='*.ext'
            )
        )
    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        
        nodes = self.parameterAsSource(parameters, self.NODES_INPUT, context)
        pfield = self.parameterAsFields(parameters, self.P_FIELD_INPUT, context)
        pfield = pfield[0]
        links = self.parameterAsSource(parameters, self.LINKS_INPUT, context)
        sfield = self.parameterAsFields(parameters, self.S_FIELD_INPUT, context)
        sfield = sfield[0]
        epanet = self.parameterAsFields(parameters, self.EPANET_INPUT, context)
        template = self.parameterAsFile(parameters, self.TMPL_INPUT, context)
        algorithm = self.parameterAsEnum(parameters, self.ALGO_INPUT, context)
        
        # OUTPUT
        
        extfile = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )
        
        # READ TEMPLATE
        myht = Htxtf(template)
        extsections = myht.read()
        
        # WRITE OPTIONS
        
        # TITLE
        
        extsections['TITLE'].append('; File generated by nettools')
        
        # INP
        
        extsections['INP'] = epanet
        
        # OPTIONS
        
        line = 'algorithm ' + self.ALGORITHMS[algorithm]
        extsections['OPTIONS'].append(line)

        
        # GET PRESSURES AND WRITE SECTION
        
        pcnt = 0
        for feature in nodes.getFeatures():
            if feature[pfield] != None:
                pcnt += 1
                line = feature['id']+' '*4 + str(feature[pfield])
                extsections['PRESSURES'].append(line)

        
        # GET SERIES AND WRITE SECTION

        scnt = 0
        for feature in links.getFeatures():
            if feature[sfield] != None:
                scnt += 1
                line = (feature['id']+' '*4 + str(feature[sfield]))
                extsections['PIPES'].append(line)

        
        # WRITE EXT FILE
        
        myht.write(extsections, extfile)
        
        msg = 'Proccesed node pressures: {},  pipes: {}.'.format(pcnt,scnt)
        feedback.pushInfo(msg)
        
        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {self.OUTPUT: extfile}
