# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessingAlgorithm,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsFeatureSink,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSink,
                       QgsGeometry,
                       QgsWkbTypes
                      )
from nettools import Network

class EpanetResultsToCsv(QgsProcessingAlgorithm):
    """
    bla bla bla
    """
    
    # DEFINE CONSTANTS
    
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
        bla bla bla.
        """
        return self.tr('Build a network (nodes and links) from an epanet file.')

    def initAlgorithm(self, config=None):
        """
         Define the inputs and outputs of the algorithm.
        """
        
        # ADD INPUT FILE
        
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Epanet file'),
                 extension='inp'
            )
        )

        # ADD NODE AND LINK SINKS
        
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
        RUN PROCESS
        """
        # INPUT
        epanetf = self.parameterAsFile(parameters, self.INPUT, context)
               
        # READ NETWORK

        network = Network()
        network.from_epanet(epanetf)
        nodes = network.nodes
        links = network.links
        
        # GENERATE NODES LAYER
        
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("elevation", QVariant.Double))
        (nodes_sink, nodes_id) = self.parameterAsSink(
            parameters,
            self.NODES_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point
            )
        
        ncnt = 0
        ntot = len(nodes)
        for node in nodes:
            #add feature to sink
            ncnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(node.get_wkt()))
            f.setAttributes([node.nodeid, node.get_type(), node.elevation])
            nodes_sink.addFeature(f, QgsFeatureSink.FastInsert) 
            if ncnt % 100 == 0:
                feedback.setProgress(50*ncnt/ntot) # Update the progress bar
        
        
        # GENERATE LINKS LAYER
        
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("start", QVariant.String))
        newfields.append(QgsField("end", QVariant.String))
        newfields.append(QgsField("type", QVariant.String))
        newfields.append(QgsField("length", QVariant.Double))
        newfields.append(QgsField("diameter", QVariant.Double))
        newfields.append(QgsField("roughness", QVariant.Double))
        (links_sink, links_id) = self.parameterAsSink(
            parameters,
            self.LINKS_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString
            )
        
        lcnt = 0
        ltot = len(links)
        for link in links:
            #add feature to sink
            lcnt += 1
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromWkt(link.get_wkt()))
            if link.get_type() in ['PIPE', 'CVPIPE']:
                f.setAttributes(
                    [link.linkid,
                    link.start,
                    link.end,
                    link.get_type(),
                    link._length,
                    link.diameter,
                    link.roughness]
                    )
            else:
                f.setAttributes(
                    [link.linkid,
                    link.start,
                    link.end,
                    link.get_type(),
                    link._length,
                    None,
                    None]
                    )
            
            links_sink.addFeature(f, QgsFeatureSink.FastInsert)
            
            if lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/ltot) # Update the progress bar
        
        msg = 'Add: {} nodes and {} links.'.format(ncnt,lcnt)
        feedback.pushInfo(msg)                

        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {self.NODES_OUTPUT: nodes_id, self.LINKS_OUTPUT: links_id}