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
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterNumber,
                       QgsWkbTypes
                      )

class ConnectByDistanceAlgorithm(QgsProcessingAlgorithm):
    """
    Connect entities by distance.
    """

    # DEFINE CONSTANTS
    SOURCE_INPUT = 'SOURCE_LAYER_INPUT'
    TARGET_INPUT = 'TARGET_LAYER_INPUT'
    CONNECTION_OUTPUT = 'CONNECTION_OUTPUT'
    MAX_CONNECTIONS = 'MAX_CONNECTIONS'
    MAX_DISTANCE = 'MAX_DISTANCE'


    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ConnectByDistanceAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'Connect_by_distance'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Connect by distance')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Demand')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'demand'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''Connect entities by minimum distance.
        The result is a layer of lines.
        The parameters are the maximum number of connections and the maximum 
        join distance.
        The source and target layers must have an id field.         
        ===
        Conecta entidades por proximidad.
        El resultado es una capa de líneas.
        Los parámetros son el número máximo de conexiones y la distancia máxima
        de conexión.
        Las capas de origen y destino deben tener un campo id.
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.SOURCE_INPUT,
                self.tr('Source layer'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
                )
            )

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET_INPUT,
                self.tr('Target layer'),
                types=[QgsProcessing.TypeVectorAnyGeometry]
                )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_CONNECTIONS,
                self.tr('Max number of connections'),
                type=QgsProcessingParameterNumber.Integer,
                defaultValue=1
                )
            )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_DISTANCE,
                self.tr('Max distance'),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0
                )
            )

        # ADD LINKS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.CONNECTION_OUTPUT,
                self.tr('Connection layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        s_ly = self.parameterAsSource(parameters, self.SOURCE_INPUT, context)
        t_ly = self.parameterAsSource(parameters, self.TARGET_INPUT, context)
        max_con = self.parameterAsInt(parameters, self.MAX_CONNECTIONS, context)
        max_dst = self.parameterAsDouble(parameters, self.MAX_DISTANCE, context)

        # CHECK CRS
        crs = s_ly.sourceCrs()
        if crs == t_ly.sourceCrs():

            # SEND INFORMATION TO THE USER
            feedback.pushInfo('='*40)
            feedback.pushInfo('CRS is {}'.format(crs.authid()))
        else:
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

        # OUTPUT LAYER
        fields= QgsFields()
        fields.append(QgsField('source', QVariant.String))
        fields.append(QgsField('target', QVariant.String))
        fields.append(QgsField('distance', QVariant.Double))
        fields.append(QgsField('n', QVariant.Int))
        (connection_sink, connection_id) = self.parameterAsSink(
            parameters,
            self.CONNECTION_OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            crs
            )

        # COMPUTE AND WRITE LINK LAYER
        f = QgsFeature()
        cnt = 0
        for s_feature in s_ly.getFeatures():
            connections = []
            for t_feature in t_ly.getFeatures():
                geo = s_feature.geometry().shortestLine(t_feature.geometry())
                distance = geo.length()
                if distance <= max_dst:
                    source_id = s_feature["id"]
                    target_id = t_feature["id"]
                    connection = (geo, source_id, target_id, distance)
                    if len(connections) < max_con:
                        connections.append(connection)
                    else:
                        connections.sort(key = lambda x: x[-1])
                        if distance < connections[-1][0]:
                            connections[-1] = connection
            for connection in connections:
                f.setGeometry(connection[0])
                f.setAttributes(connection[1:] + tuple(len(connections)))
                connection_sink.addFeature(f)
                cnt += 1

            # SHOW PROGRESS
            feedback.setProgress(100*cnt/s_ly.featureCount())

        # SHOW PROGRESS
        feedback.pushInfo(f'Source #: {s_ly.featureCount()}.')
        feedback.pushInfo(f'Target #: {t_ly.featureCount()}.')
        feedback.pushInfo(f'Link #: {cnt}.')

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.CONNECTION_OUTPUT: connection_id}
