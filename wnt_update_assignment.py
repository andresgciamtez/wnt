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
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterField,
                       QgsWkbTypes
                      )

class UpdateAssignmentAlgorithm(QgsProcessingAlgorithm):
    """
    Update demands.
    """

    # DEFINE CONSTANTS
    SOURCE_INPUT = 'SOURCE_LAYER_INPUT'
    SOURCE_FIELD = 'SOURCE_LAYER_FIELD'
    TARGET_INPUT = 'TARGET_LAYER_INPUT'
    ASSIGN_INPUT = 'ASSIGNMENT_LAYER_INPUT'
    ASSIGN_OUTPUT = 'ASSIGNMENT_LAYER_OUTPUT'
    TARGET_OUTPUT = 'TARGET_LAYER_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return UpdateAssignmentAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'update_assignment'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Update assignment')

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
        return self.tr('''Update assignments.
        Recomputing demand value in a node layer, from an assignment layer.
        The start and end points in the assignment are updated.
        ===
        Actualiza la asignación (de demanda).
        Recalcula los valores de la demanda en una capa de nodos a partir de 
        una capa de assignaciones.
        La posición de los extremos de las asignaciones son actualizadas.
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
                self.SOURCE_FIELD,
                self.tr('Source field'),
                'value',
                self.SOURCE_INPUT
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.TARGET_INPUT,
                self.tr('Target layert'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.ASSIGN_INPUT,
                self.tr('Assignment layert'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )

        # ADD PAIRS FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.ASSIGN_OUTPUT,
                self.tr('Updated assignment layer')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.TARGET_OUTPUT,
                self.tr('Updated target layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        slayer = self.parameterAsSource(parameters, self.SOURCE_INPUT, context)
        sfield = self.parameterAsString(parameters, self.SOURCE_FIELD, context)
        tlayer = self.parameterAsSource(parameters, self.TARGET_INPUT, context)
        alayer = self.parameterAsSource(parameters, self.ASSIGN_INPUT, context)

        # CHECK CRS
        crs = slayer.sourceCrs()
        if crs == tlayer.sourceCrs() == alayer.sourceCrs():

            # SEND INFORMATION TO THE USER
            feedback.pushInfo('='*40)
            feedback.pushInfo('CRS is {}'.format(crs.authid()))
        else:
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

        # OUTPUT
        afields = QgsFields()
        for field in ['source', 'target', sfield]:
            afields.append(QgsField(field, QVariant.String))
        (assign_sink, assign_id) = self.parameterAsSink(
            parameters,
            self.ASSIGN_OUTPUT,
            context,
            afields,
            QgsWkbTypes.LineString,
            crs
            )
        tfields = tlayer.fields()
        if sfield not in tfields:
            tfields.append(QgsField(sfield, QVariant.String))
        (target_sink, target_id) = self.parameterAsSink(
            parameters,
            self.TARGET_OUTPUT,
            context,
            tfields,
            QgsWkbTypes.Point,
            crs
            )

        # READ DATA
        sources = {}
        targets = {}

        for f in alayer.getFeatures():
            if not f["source"] in sources:
                sources[f["source"]] = None
            else:
                msg = 'Duplicated source {} assignation.'.format(f["source"])
                feedback.reportError(msg)
            if not f["target"] in targets:
                targets[f["target"]] = None

      # SHOW PROGRESS
        feedback.setProgress(20)

        # STORE [POINT, DEMAND]
        for f in slayer.getFeatures():
            if f["id"] in sources:
                sources[f["id"]] = [QgsPoint(f.geometry().asPoint()), f[sfield]]

        # SHOW PROGRESS
        feedback.setProgress(40)

        # STORE [POINT, DEMAND=0]
        for f in tlayer.getFeatures():
            if f["id"] in targets:
                targets[f["id"]] = [QgsPoint(f.geometry().asPoint()), 0]

        # SHOW PROGRESS
        feedback.setProgress(60)

        # WRITE UPDATED ASSIGNEMENT
        for f in alayer.getFeatures():

            # ACCUMULATE DEMAND
            targets[f["target"]][1] += sources[f["source"]][1]

            # WRITE ASSIGNEMENT
            g = QgsFeature()
            spoint = sources[f["source"]][0]
            tpoint = targets[f["target"]][0]
            g.setGeometry(QgsLineString([spoint, tpoint]))
            attrib = [f["source"], f["target"], sources[f["source"]][1]]
            g.setAttributes(attrib)
            assign_sink.addFeature(g)

        # SHOW PROGRESS
        feedback.setProgress(80)

        # WRITE UPDATED TARGET
        for f in tlayer.getFeatures():
            g = QgsFeature()
            attr = f.attributes()
            attr.append(targets[f["id"]][1])
            g.setAttributes(attr)
            target_sink.addFeature(g)

        # SHOW PROGRESS
        feedback.setProgress(100)

        # SHOW PROGRESS
        feedback.pushInfo('Source #: {}.'.format(slayer.featureCount()))
        feedback.pushInfo('Target #: {}.'.format(tlayer.featureCount()))
        feedback.pushInfo('Assignment #: {}.'.format(alayer.featureCount()))
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.ASSIGN_OUTPUT: assign_id, self.TARGET_OUTPUT: target_id}
