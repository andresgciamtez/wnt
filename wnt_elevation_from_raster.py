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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField
                      )
 
class ElevationFromRasterAlgorithm(QgsProcessingAlgorithm):
    """
    Get node elevation from DEM.
    """

    # DEFINE CONSTANTS

    NODES_INPUT = 'NODES_INPUT'
    DEM_INPUT = 'DEM_INPUT'
    ELEV_FIELD_INPUT = 'ELEV_FIELD_INPUT'
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
        return ElevationFromRasterAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'elevation_from_raster'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Node elevation from DEM')

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
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Get nodes elevation from DEM raster.')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """
        
        # ADD THE INPUT SOURCES
        
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODES_INPUT,
                self.tr('Input nodes vector layer'),
                types=[QgsProcessing.TypeVectorPoint]
            )
        )
        self.addParameter(
            QgsProcessingParameterField (
                self.ELEV_FIELD_INPUT,
                self.tr('Field where write elevation'),
                'elevation',
                self.NODES_INPUT
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM_INPUT,
                self.tr('Input DEM raster layer')
            )
        )
        
        #ADD THE OUTPUT SINK
        
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Output nodes layer with elevation'),
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Run the process.
        """
        
        # INPUT
        
        nodes = self.parameterAsSource(parameters, self.NODES_INPUT, context)
        dem = self.parameterAsRasterLayer(parameters, self.DEM_INPUT, context)
        efield = self.parameterAsString(parameters, self.ELEV_FIELD_INPUT, context)
        
        # OUTPUT
        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            nodes.fields(),
            nodes.wkbType(),
            nodes.sourceCrs()
            )

        # MAIN LOOP READ/WRITE POINTS
        
        feedback.pushInfo('CRS is {}'.format(nodes.sourceCrs().authid()))
        tot = nodes.featureCount()
        pcnt = 0
        ncnt = 0
        
        for feat in  nodes.getFeatures():
            val, res = dem.dataProvider().sample(feat.geometry().asPoint(), 1)
            if res:
                pcnt += 1
                feat[efield] = val
                sink.addFeature(feat, QgsFeatureSink.FastInsert)
            else:
                ncnt += 1
            
            if (pcnt+ncnt) % 100 == 0:
                feedback.setProgress(100*(pcnt+ncnt)/tot) # Update the progress bar
        
        msg = 'Proccesed nodes: {},  skipped: {}.'.format(pcnt,ncnt)
        feedback.pushInfo(msg)
        
        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {self.OUTPUT: dest_id}
