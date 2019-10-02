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

from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsWkbTypes
                       )
from . import tools

class NodeDegreesAlgorithm(QgsProcessingAlgorithm):
    """
    Build an epanet model file from node and link layers.
    """

    # DEFINE CONSTANTS
    NODE_INPUT = 'NODE_INPUT'
    LINK_INPUT = 'LINK_INPUT'
    NODE_OUTPUT = 'NODE_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return NodeDegreesAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'node_degrees'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Node degrees')

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Graph')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'graph'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        msg = 'Calculate the node degrees of a network and generate a node '
        msg += 'layer with a field containing degrees.\n'
        msg += 'Note: the degree is the number of links (edges) connected '
        msg += 'to a node.\n'
        msg += 'Special cases:\n'
        msg += '- Orphan nodes have degree 0\n'
        msg += '- Leaf nodes have degree 1\n'
        msg += '- Continuity nodes have degree 2\n'
        return self.tr(msg)

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT NETWORK (NODES AND LINKS)
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODE_INPUT,
                self.tr('Network node layer input'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINK_INPUT,
                self.tr('Network links layer input'),
                [QgsProcessing.TypeVectorLine]
                )
            )

        # ADD NODE AND LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODE_OUTPUT,
                self.tr('Node degree layer')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        nodelay = self.parameterAsSource(parameters, self.NODE_INPUT, context)
        linklay = self.parameterAsSource(parameters, self.LINK_INPUT, context)

        # CHECK CRS
        crs = nodelay.sourceCrs()
        if crs == linklay.sourceCrs():

            # SEND INFORMATION TO THE USER
            feedback.pushInfo('='*40)
            feedback.pushInfo('CRS is {}'.format(crs.authid()))
        else:
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

        # OUTPUT
        newfields = nodelay.fields()
        if 'degree' not in nodelay.fields().names():
            newfields.append(QgsField('degree', QVariant.Int))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.NODE_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point,
            crs
            )

        # DEFINE NETWORK
        net = tools.Network()

        # LOAD LAYERS
        nofn = nodelay.featureCount()
        nofl = linklay.featureCount()

        # ADD NODES
        cnt = 0
        for f in nodelay.getFeatures():
            cnt += 1
            net.nodes.append(tools.Node(f['id']))

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(33*cnt/nofn)

        # ADD LINKS
        cnt = 0
        for f in linklay.getFeatures():
            cnt += 1
            net.links.append(tools.Link(f['id'], f['start'], f['end']))

            # SHOW POROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(33+33*cnt/nofl)

        # CALCULATE DEGREES
        degrees = net.degree()

        # WRITE NODE DEGREES
        cnt = 0
        for f in nodelay.getFeatures():
            cnt += 1
            attr = f.attributes()
            attr.extend([degrees[f['id']]])
            f.setAttributes(attr)
            node_sink.addFeature(f)

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(67+33*cnt/nofn)

        # SHOW INFO
        msg = 'Processed: {} nodes and {} links'.format(nofn, nofl)
        feedback.pushInfo(msg)
        msg = 'Write: {} node degrees'.format(nofn)
        feedback.pushInfo(msg)
        msg = 'Min degree: {} Max degree: {}'
        msg = msg.format(min(degrees.values()), max(degrees.values()))
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id}
