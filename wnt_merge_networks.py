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
from qgis.core import (QgsFeature,
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource
                      )

class MergeNetworksAlgorithm(QgsProcessingAlgorithm):
    """
    Built a network from lines.
    """

    # DEFINE CONSTANTS
    NODE1_INPUT = 'NODE1_INPUT'
    LINK1_INPUT = 'LINK1_INPUT'
    NODE2_INPUT = 'NODE2_INPUT'
    LINK2_INPUT = 'LINK2_INPUT'
    NODE_OUTPUT = 'NODE_OUTPUT'
    LINK_OUTPUT = 'LINK_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return MergeNetworksAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'merge_networks'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Merge networks')

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
        return self.tr('''Merge 2 networks from nodes and lines.
        Connection nodes must have the same ID.
        
        Note: The network is generated even if the distance between the 
        connection points is not zero. The max distance is shown.
        
        Tip: Check the final network with *Validate*

        ===
        Combina 2 redes a partir de sus nodos y líneas.
        Los nodos de conexión deben tener la misma ID.
        
        Nota: La red se genera, aunque la distancia entre los puntos de 
        conexión no sea cero. La distancia máxima se muestra en el registro.
        
        Consejo: Revise la red final con *Validar*        
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODE1_INPUT,
                self.tr('First node layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINK1_INPUT,
                self.tr('First link layer input'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODE2_INPUT,
                self.tr('Second node layer input'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINK2_INPUT,
                self.tr('Second link layer input'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )

        # ADD NODE AND LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODE_OUTPUT,
                self.tr('Merged node layer'),
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINK_OUTPUT,
                self.tr('Merged link layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        n1lay = self.parameterAsSource(parameters, self.NODE1_INPUT, context)
        l1lay = self.parameterAsSource(parameters, self.LINK1_INPUT, context)
        n2lay = self.parameterAsSource(parameters, self.NODE2_INPUT, context)
        l2lay = self.parameterAsSource(parameters, self.LINK2_INPUT, context)

        # CHECK CRS
        crs = n1lay.sourceCrs()
        if crs == l1lay.sourceCrs() == n2lay.sourceCrs() == l2lay.sourceCrs():

            # SEND INFORMATION TO THE USER
            feedback.pushInfo('='*40)
            feedback.pushInfo('CRS is {}'.format(crs.authid()))
        else:
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

        # GENERATE MERGED NODE LAYER
        newfields = n1lay.fields()
        for field in n2lay.fields():
            if field not in newfields:
                newfields.append(field)
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.NODE_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point,
            crs
            )

        # GENERATE MERGED LINK LAYER
        newfields = l1lay.fields()
        for field in l2lay.fields():
            if field not in newfields:
                newfields.append(field)
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.LINK_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs
            )

        # ADD FEATURES
        f = QgsFeature()
        g = QgsFeature()

        # CHECK DISTANCE
        dmax = 0
        ndmax = None

        # ADD NODES FROM FIRST NODE LAYER
        cnt = 0
        over = 0
        nofn = n1lay.featureCount()+n2lay.featureCount()
        nodes1 = set()
        for f in n1lay.getFeatures():
            cnt += 1
            nodes1.add(f['id'])
            node_sink.addFeature(f)

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(50*cnt/nofn)

        # ADD FROM SECOND NODE LAYER
        for f in n2lay.getFeatures():
            cnt += 1
            if not f['id'] in nodes1:
                node_sink.addFeature(f)
            else:

                # EXISTING NODE SO CHECK OVERLAPPING
                for g in n1lay.getFeatures():
                    if g['id'] == f['id']:
                        over += 1
                        dist = f.geometry().distance(g.geometry())
                        if dist > dmax:
                            dmax = dist
                            ndmax = f['id']

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(50*cnt/nofn)

        # SHOW DISTANCE MAX
        if dist > 0:
            msg = 'WARNING: Connection node {} distance: {}'
            msg = msg.format(ndmax, dmax)
            feedback.pushInfo(msg)

        # ADD LINKS
        cnt = 0
        nofl = l1lay.featureCount()+l2lay.featureCount()
        for layer in [l1lay, l2lay]:
            for f in layer.getFeatures():
                cnt += 1
                link_sink.addFeature(f)

                # SHOW PROGRESS
                if cnt % 100 == 0:
                    feedback.setProgress(50+50*cnt/nofl)

        # SHOW INFO
        msg = 'Read: {} nodes and {} links'.format(nofn, nofl)
        feedback.pushInfo(msg)
        msg = 'Added: {} nodes and {} links'.format(nofn-over, nofl)
        feedback.pushInfo(msg)
        msg = 'Connection nodes: {}'.format(over, nofl)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id, self.LINK_OUTPUT: link_id}
