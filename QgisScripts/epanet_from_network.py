# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFileDestination)
import processing
from nettools import Node, Link, Network

class EpanetFromNetwork(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    NODES_INPUT = 'NODES_INPUT'
    LINKS_INPUT = 'LINKS_INPUT'
    TEMPL_INPUT = 'TEMPL_INPUT'
    OUTPUT = 'OUTPUT'
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return EpanetFromNetwork()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'Epanet_from_network'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Epanet from network')

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
        msg = "Make an epanet inp file from nodes and links. \n"
        msg += "Pipe diameter and roughness are ignored."
        return self.tr(msg)

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
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINKS_INPUT,
                self.tr('Input links layer'),
                [QgsProcessing.TypeVectorLine]
            )
        )
        self.addParameter(
            QgsProcessingParameterFile (
                self.TEMPL_INPUT,
                self.tr('Epanet template file'),
                extension='inp'
            )
        )
        # Adding a feature sink in which to store our processed results.
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Epanet model file'),
                fileFilter='*.inp'
            )
        )
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # INPUT
        
        nodesinput = self.parameterAsSource(parameters, self.NODES_INPUT, context)
        linksinput = self.parameterAsSource(parameters, self.LINKS_INPUT, context)
        templinput = self.parameterAsFile(parameters, self.TEMPL_INPUT, context)
        
        # OUTPUT
        
        epanetfn = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )
        
        # BUILD NETWORK
        
        newnet = Network()
        
        for f in nodesinput.getFeatures():
            newnode = Node(f['id'])
            newnode.set_wkt(f.geometry().asWkt())
            msg = 'Bad node type'
            assert f['type'] in ['JUNCTION', 'RESERVOIR', 'TANK'], msg
            newnode.set_type(f['type'])
            newnode.elevation = f['elevation']
            newnet.nodes.append(newnode)
        
        for f in linksinput.getFeatures():
            newlink = Link(f['id'],f['start'],f['end'])
            newlink.set_wkt(f.geometry().asWkt())
            msg = 'Bad link type'
            assert f['type'] in ['PIPE', 'PUMP', 'PRV', 'PSV', 'PBV', 'FCV', \
                                'TCV','GPV'], msg
            newlink.set_type(f['type'])
            newnet.links.append(newlink)
               
        newnet.to_epanet(epanetfn, templinput)
        
        epanetfn = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )
        
        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {'OUTPUT': epanetfn}
