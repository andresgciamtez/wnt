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
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterField,
                       QgsProcessingParameterString
                      )
from . utils_tin import TIN

class ElevationFromTINAlgorithm(QgsProcessingAlgorithm):
    """
    Set the node elevation from a TIN in LandXML format.
    """

    # DEFINE CONSTANTS
    NODE_INPUT = 'NODE_INPUT'
    ELEV_FIELD = 'ELEV_FIELD'
    TIN_INPUT = 'TIN_INPUT'
    SURFACE_NAME = 'SURFACE_NAME'
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
        return ElevationFromTINAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'elevation_from_tin'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Node elevation from TIN (LandXML)')

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
        return self.tr('''Set network node elevation from a TIN surface (LandXML).
                       
        http://www.landxml.org/
        ===
        Añade elevación a los nodos de la red desde una superfice TIN (LandXML).
        
        http://www.landxml.org/
        ''')

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
                self.tr('Elevation field'),
                'elevation',
                self.NODE_INPUT
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.TIN_INPUT,
                self.tr('landXML file'),
                extension='xml'
                )
            )
        self.addParameter(
            QgsProcessingParameterString(
                self.SURFACE_NAME,
                self.tr('Surface name (if empty, first found)'),
                defaultValue='',
                multiLine=False,
                optional=True
                )
            )

        #ADD THE OUTPUT SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Nodes with elevation layer')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodelayer = self.parameterAsSource(parameters, self.NODE_INPUT, context)
        efield = self.parameterAsString(parameters, self.ELEV_FIELD, context)
        tinlayer = self.parameterAsFile(parameters, self.TIN_INPUT, context)
        sname = self.parameterAsString(parameters, self.SURFACE_NAME, context)

        # SEND INFORMATION TO THE USER
        crs = nodelayer.sourceCrs()
        feedback.pushInfo('='*40)
        feedback.pushInfo('CRS is {}'.format(crs.authid()))

        # OUTPUT
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            nodelayer.fields(),
            nodelayer.wkbType(),
            nodelayer.sourceCrs()
            )

        # READ NODES
        points = []
        cnt = 0

        for f in  nodelayer.getFeatures():
            point = f.geometry().asPoint().x(), f.geometry().asPoint().y()
            points.append(point)
        surface = TIN()
        surface.from_landxml(tinlayer, sname)
        elevations = surface.elevations(points)

        # SHOW PROGRESS
        msg = 'Total nodes: {}.'.format(len(points))
        feedback.pushInfo(msg)
        feedback.setProgress(50)

        # WRITE NODES
        for f, z in zip(nodelayer.getFeatures(), elevations):
            f[efield] = z
            sink.addFeature(f) # , QgsFeatureSink.FastInsert)
            if not z:
                cnt += 1

        # SHOW PROGRESS
        feedback.setProgress(100)
        msg = 'Skipped nodes: {}.'.format(cnt)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: dest_id}
