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

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsPoint,
                       QgsLineString,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterDistance,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsWkbTypes
                      )

class HydrantPairsAlgorithm(QgsProcessingAlgorithm):
    """
    Built a network from lines.
    """

    # DEFINE CONSTANTS
    HYD_INPUT = 'HYDRANT_INPUT'
    ID_FIELD = 'HIDRANT_ID_FIELD'
    MAX_DIST = 'MAX_DIST'
    PAIRS_OUTPUT = 'PAIRS_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return HydrantPairsAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'hydrant_pairs'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Hydrant pairs')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Fire')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'fire'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''Generate pairs of hydrants from a node layer.
        The result is a line layer containing lines (it allows to check that 
        they run over public space) and node labels.
        
        Points separated more than max distance are discarded.        
        ===
        Genera un pare de hidrantes a partir de una capa de nodos.
        El resultado es una capa de líneas (que permite comprobar que estas 
        discurren por espacio público).
        
        Los puntos separados más de la distancia máxima son descartados.
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.HYD_INPUT,
                self.tr('Hydrant layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.ID_FIELD,
                self.tr('Hiydrant ID field'),
                'id',
                self.HYD_INPUT
                )
            )
        self.addParameter(
            QgsProcessingParameterDistance(
                self.MAX_DIST,
                self.tr('Maximum hydrant separation'),
                defaultValue=200,
                minValue=0.1,
                maxValue=10000
                )
            )
        # ADD PAIRS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.PAIRS_OUTPUT,
                self.tr('Hydrant pairs layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        hydlayer = self.parameterAsSource(parameters, self.HYD_INPUT, context)
        idfield = self.parameterAsString(parameters, self.ID_FIELD, context)
        maxdist = self.parameterAsDouble(parameters, self.MAX_DIST, context)

        # SEND INFORMATION TO THE USER
        feedback.pushInfo('='*40)
        crsid = hydlayer.sourceCrs().authid()
        if crsid:
            feedback.pushInfo('CRS is {}.'.format(crsid))
        else:
            feedback.pushInfo('WARNING: CRS is not set!')

        # READ HYDRANTS
        hydrants = []
        pairs = []
        for f in hydlayer.getFeatures():
            hydrants.append((f[idfield], f.geometry().asPoint()))

        # CALCULATE PAIRS
        for i in range(len(hydrants)-1):
            for j in range(i+1, len(hydrants)):
                dist = hydrants[i][1].distance(hydrants[j][1])
                if dist <= maxdist:
                    pairs.append((hydrants[i], hydrants[j], dist))

        # SHOW INFO
        feedback.pushInfo('Read: {} hydrants.'.format(len(hydrants)))

        # GENERATE PAIRS LAYER
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.String))
        fields.append(QgsField("hydrant_1", QVariant.String))
        fields.append(QgsField("hydrant_2", QVariant.String))
        fields.append(QgsField("distance", QVariant.Double))
        (pairs_sink, pairs_id) = self.parameterAsSink(
            parameters,
            self.PAIRS_OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            hydlayer.sourceCrs()
            )

        # SHOW PROGRESS
        feedback.setProgress(50)

        # ADD FEATURES
        f = QgsFeature()
        cnt = 0
        for pair in pairs:
            p1 = QgsPoint(pair[0][1])
            p2 = QgsPoint(pair[1][1])
            f.setGeometry(QgsLineString([p1, p2]))
            f.setAttributes([str(cnt), pair[0][0], pair[1][0], pair[2]])
            pairs_sink.addFeature(f)
            cnt += 1

        # SHOW PROGRESS
        feedback.setProgress(100)
        feedback.pushInfo('Pairs #: {}.'.format(cnt))
        feedback.pushInfo('Pairs layer was generated successfully.')
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.PAIRS_OUTPUT: pairs_id}
