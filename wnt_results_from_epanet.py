# -*- coding: utf-8 -*-

"""
/***************************************************************************
 WaterNetworkTools
                                 A QGIS plugin
 Water Network Modelling Utilities
 
                              -------------------
        begin                : 2019-07-19
        copyright            : (C) 2019 by Andrés García Martínez
        email                : ppnoptimizer@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Andrés García Martínez'
__date__ = '2019-07-19'
__copyright__ = '(C) 2019 by Andrés García Martínez'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingParameterEnum,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)                      


class ResultsFromEpanetAlgorithm(QgsProcessingAlgorithm):
    """
    Import epanet result from epanet toolkit.
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
        return ResultsFromEpanetAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'results_from_epanet'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Results from epanet')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Water Network tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'wnt'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('Build results layers (nodes and links).')

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
               
        # OPEN TOOLKIK

        
        
        # GENERATE NODES LAYER
        
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.String))
        newfields.append(QgsField("flow", QVariant.Double))
        newfields.append(QgsField("head", QVariant.Double))
        newfields.append(QgsField("pressure", QVariant.Double))
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
        newfields.append(QgsField("flow", QVariant.Double))
        newfields.append(QgsField("velocity", QVariant.Double))
        newfields.append(QgsField("unit_headloss", QVariant.Double))
        newfields.append(QgsField("friction_factor", QVariant.Double))
        newfields.append(QgsField("status", QVariant.String))
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
