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

from math import inf
from qgis.PyQt.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsPoint,
                       QgsLineString,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsWkbTypes
                      )

class AssignDemandAlgorithm(QgsProcessingAlgorithm):
    """
    Assignate demands.
    """

    # DEFINE CONSTANTS
    SOURCE_INPUT = 'SOURCE_LAYER_INPUT'
    SOURCE_FIELDS = 'SOURCE_FIELDS'
    TARGET_INPUT = 'TARGET_LAYER_INPUT'
    ASSIGN_OUTPUT = 'ASSIGNMENT_LAYER_OUTPUT'
    NODE_OUTPUT = 'NODE_LAYER_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return AssignDemandAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'assign_demand'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Assign demand')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Assign')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'assign'

    def shortHelpString(self):
        """
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''Generate demand assignments.
        The result is a layer containing connecting lines between sources and 
        target layers, and an updated node layer. The assignment criterion is 
        the minimum distance.
        Both source and target layer have to have an id field.

        Tip: The assignment can be edit using the *update* process.         
        ===
        Genera asignaciones de demanda.
        El resultado consiste en una capa de líneas que conectad las fuentes y
        los destinos de la demanda, y una capa de nodos con la demanda 
        actualizada. El criterio de asignación es el de mínima distancia.
        Las capas source and target deben tener un campo id.
        
        Consejo: Las asignaciones pueden ser actualizadas con *update*.
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
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.SOURCE_FIELDS,
                self.tr('Source demand fields'),
                None,
                self.SOURCE_INPUT,
                allowMultiple=True
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET_INPUT,
                self.tr('Target layer'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )

        # ADD PAIRS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ASSIGN_OUTPUT,
                self.tr('Assignment layer')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODE_OUTPUT,
                self.tr('Target with demands layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        slayer = self.parameterAsSource(parameters, self.SOURCE_INPUT, context)
        sfields = self.parameterAsFields(parameters, self.SOURCE_FIELDS, context)
        tlayer = self.parameterAsSource(parameters, self.TARGET_INPUT, context)

        # CHECK CRS
        crs = slayer.sourceCrs()
        if crs == tlayer.sourceCrs():

            # SEND INFORMATION TO THE USER
            feedback.pushInfo('='*40)
            feedback.pushInfo('CRS is {}'.format(crs.authid()))
        else:
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

        # OUTPUT LAYERS
        fields = QgsFields()
        fields.append(QgsField('source', QVariant.String))
        fields.append(QgsField('target', QVariant.String))
        for field in sfields:
            fields.append(QgsField(field, QVariant.Double))
        (assignment_sink, assignment_id) = self.parameterAsSink(
            parameters,
            self.ASSIGN_OUTPUT,
            context,
            fields,
            QgsWkbTypes.LineString,
            crs
            )

        fields = tlayer.fields()
        for field in sfields:
            fields.append(QgsField(field, QVariant.Double))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.NODE_OUTPUT,
            context,
            fields,
            QgsWkbTypes.Point,
            crs
            )

        # ASSIGN, ACCUMULATE AND WRITE ASSIGNMENT LAYER
        values = {}
        for tfeature in tlayer.getFeatures():
            for field in sfields:
                values[(tfeature["id"], field)] = 0.0
        cnt = 0
        for sfeature in slayer.getFeatures():
            sxy = sfeature.geometry().asPoint()
            cdist = inf
            cfeature = None
            for tfeature in tlayer.getFeatures():
                dist = tfeature.geometry().asPoint().distance(sxy)
                if dist < cdist:
                    cdist = dist
                    cfeature = tfeature
            f = QgsFeature()
            spoint = QgsPoint(sxy)
            cpoint = QgsPoint(cfeature.geometry().asPoint())
            f.setGeometry(QgsLineString([spoint, cpoint]))
            attr = [sfeature["id"], cfeature["id"]]
            for field in sfields:
                attr.append(sfeature[field])
                values[(cfeature["id"], field)] += sfeature[field]
            f.setAttributes(attr)
            assignment_sink.addFeature(f)
            cnt += 1

            # SHOW PROGRESS
            feedback.setProgress(50*cnt/slayer.featureCount())

        # WRITE NODE LAYER
        cnt = 0
        for tfeature in tlayer.getFeatures():
            f = QgsFeature()
            attr = tfeature.attributes()
            for field in sfields:
                attr.append(values[(tfeature["id"], field)])
            f = tfeature
            f.setAttributes(attr)
            node_sink.addFeature(f)
            cnt += 1

            # SHOW PROGRESS
            feedback.setProgress(50+50*cnt/tlayer.featureCount())

        # SHOW PROGRESS
        feedback.pushInfo('Source #: {}.'.format(slayer.featureCount()))
        feedback.pushInfo('Target #: {}.'.format(tlayer.featureCount()))
        nncnt = sum((1 for x in values if abs(values[x]) > 0))
        feedback.pushInfo('Not null assignment #: {}.'.format(nncnt))
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.ASSIGN_OUTPUT: assignment_id, self.NODE_OUTPUT: node_id}
