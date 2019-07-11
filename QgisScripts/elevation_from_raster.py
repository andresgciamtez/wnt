# -*- coding: utf-8 -*-
"""
NETTOOLS IMPORT/EXPORT WATER NETWORK DATA FROM/TO GIS
Andrés García Martínez (ppnoptimizer@gmail.com)
Licensed under the Apache License 2.0. http://www.apache.org/licenses/
"""
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsProcessing,
                       QgsProcessingFeedback,
                       QgsProcessingAlgorithm,
                       QgsFeatureSink,
                       QgsFields,
                       QgsField,
                       QgsFeature,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterString, 
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingException,
                       QgsGeometry,
                       QgsWkbTypes
                      )
from nettools import Network
 
class ElevationFromRaster(QgsProcessingAlgorithm):
    """
    Get elevation form raster.
    
    Return
    ------
    A Nodes Point vector layer. 
    """
    NODES_INPUT = 'NODES_INPUT'
    RASTER_INPUT = 'RASTER_INPUT'
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
        # 'INPUT' is the recommended name for the main input parameter.
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
                self.tr('Field containing elevation'),
                'elevation',
                self.NODES_INPUT
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.RASTER_INPUT,
                self.tr('Input DEM raster layer')
            )
        )
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
        
        input = self.parameterAsSource(parameters, self.NODES_INPUT, context)
        dem = self.parameterAsRasterLayer(parameters, self.RASTER_INPUT, context)
        elevf = self.parameterAsString(parameters, self.ELEV_FIELD_INPUT, context)
        flds = input.fields
        
        # OUTPUT
        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            input.fields(),
            input.wkbType(),
            input.sourceCrs()
            )

        # MAIN LOOP READ/WRITE POINTS
        feedback.pushInfo('*'*4)
        feedback.pushInfo('CRS is {}'.format(input.sourceCrs().authid()))
        pcnt = 0
        ncnt = 0
        
        for feat in  input.getFeatures():
            pcnt += 1
            val, res = dem.dataProvider().sample(feat.geometry().asPoint(), 1)
            if not(res):
                ncnt += 1
            feat[elevf] = val
            sink.addFeature(feat, QgsFeatureSink.FastInsert)
        
        feedback.pushInfo('Proccesed nodes: {},  skipped: {}.'.format(pcnt,ncnt))
        feedback.pushInfo('*'*4)
        
        # PROCCES CANCELED
        
        if feedback.isCanceled():
            return {}
        
        # OUTPUT

        return {self.OUTPUT: dest_id}