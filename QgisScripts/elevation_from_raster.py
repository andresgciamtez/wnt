# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsFeatureSink,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField
                      )
 
class ElevationFromRaster(QgsProcessingAlgorithm):
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
        return ElevationFromRaster()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'elevationfromraster'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Get nodes elevation from raster')

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