# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterString, 
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsGeometry,
                       QgsWkbTypes
                      )
from nettools import Network

class NetworkFromEpanet(QgsProcessingAlgorithm):
    """
    Built a network from an epanet file.
    
    Return
    ------
    links vector layer
    nodes vector layer
    """
    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    
    INPUT = 'INPUT'
    NODES_OUTPUT = 'NODES_OUTPUT'
    LINKS_OUTPUT = 'LINKS_OUTPUT'
    
    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        createInstance must return a new copy of algorithm.
        """
        return NetworkFromEpanet()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'networkfromepanet'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Build a network from an epanet file')

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
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Build a network (nodes and links) from an epanet file.')

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and outputs of the algorithm.
        """
        # 'INPUT' is the recommended name for the main input
        # parameter.
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Epanet file'),
                 extension='inp'
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODES_OUTPUT,
                self.tr('Nodes')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINKS_OUTPUT,
                self.tr('Links'),
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        # INPUT
        input = self.parameterAsFile(parameters, self.INPUT, context)
               
        # READ NETWORK
        print('*',input)
        newnetwork = Network()
        newnetwork.from_epanet(input)
        nodes,links = newnetwork.nodes,newnetwork.links
        
        # GENERATE NODES LAYER
        
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("elevation", QVariant.Double))
        (nodes_sink, nodes_dest_id) = self.parameterAsSink(
            parameters,
            self.NODES_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point
            )
        for node in nodes:
            #add feature to sink
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(node.get_wkt()))
            f.setAttributes([node.nodeid, node.get_type(), node.elevation])
            nodes_sink.addFeature(f, QgsFeatureSink.FastInsert) 
        
        # GENERATE LINKS LAYER
        
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("start", QVariant.String))
        newfields.append(QgsField("end", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("length", QVariant.Double))
        newfields.append(QgsField("diameter", QVariant.Double))
        newfields.append(QgsField("roughness", QVariant.Double))
        (links_sink, links_dest_id) = self.parameterAsSink(
            parameters,
            self.LINKS_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString
            )
        for link in links:
            #add feature to sink
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(link.get_wkt()))
            if link.get_type() in ['PIPE', 'CVPIPE']:
                print('*', link.linkid,link.diameter)
                f.setAttributes(
                    [link.linkid,
                    link.start,
                    link.end,
                    link.get_type(),
                    link.get_length(),
                    link.diameter,
                    link.roughness]
                    )
            else:
                f.setAttributes(
                    [link.linkid,
                    link.start,
                    link.end,
                    link.get_type(),
                    link.get_length(),
                    None,
                    None]
                    )
            
            links_sink.addFeature(f, QgsFeatureSink.FastInsert) 

        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {'NODES_OUTPUT': nodes_dest_id,'LINKS_OUTPUT': links_dest_id}