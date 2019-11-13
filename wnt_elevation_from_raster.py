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
    Set the node elevation from a DEM in raster format.
    """

    # DEFINE CONSTANTS
    NODE_INPUT = 'NODE_INPUT'
    DEM_INPUT = 'DEM_INPUT'
    ELEV_FIELD = 'ELEV_FIELD'
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
        return self.tr('Modify')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'modify'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('Set node elevation from DEM in raster format.')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT SOURCES
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODE_INPUT,
                self.tr('Node vector layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.ELEV_FIELD,
                self.tr('Field where will write elevation'),
                'elevation',
                self.NODE_INPUT
                )
            )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DEM_INPUT,
                self.tr('DEM raster layer input')
                )
            )

        #ADD THE OUTPUT SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Node with elevation layer'),
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodes = self.parameterAsSource(parameters, self.NODE_INPUT, context)
        dem = self.parameterAsRasterLayer(parameters, self.DEM_INPUT, context)
        efield = self.parameterAsString(parameters, self.ELEV_FIELD, context)

        # CHECK CRS
        crs = nodes.sourceCrs()
        if crs == dem.crs():

            # SEND INFORMATION TO THE USER
            feedback.pushInfo('='*40)
            feedback.pushInfo('CRS is {}'.format(crs.authid()))
        else:
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

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

            # SHOW PROGRESS
            if (pcnt+ncnt) % 100 == 0:
                feedback.setProgress(100*(pcnt+ncnt)/tot)
        msg = 'Proccesed nodes: {}. skipped: {}.'.format(pcnt, ncnt)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: dest_id}
