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
from qgis.core import (QgsField,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsWkbTypes
                       )
from . import utils_core as tools

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
        return self.tr('''Calculate the graph-network node degrees.
        The degree is the number of links (edges) connected to a node.
        Cases:
        - Orphan nodes have degree 0
        - Leaf nodes have degree 1
        - Continuity nodes have degree 2
        
        Degrees are stored in the 'degree' field.
        ===
        Calcula el grado de los nodos del gráfico de red.
        (El grado es el número de líneas conectados al nodo.)
        Casos particulares:
        - Los nodos huérfanos tienen grado 0
        - Los nodos hoja tienen grado 1
        - Los nodos de continuidad tienen grado 2

        Los grados se almacenan en el campo 'degree'.
        ''')

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
            nodelay.sourceCrs()
            )

        # DEFINE NETWORK
        net = tools.WntNetwork()

        # LOAD LAYERS
        nofn = nodelay.featureCount()
        nofl = linklay.featureCount()

        # ADD NODES
        cnt = 0
        for f in nodelay.getFeatures():
            cnt += 1
            net.add_node(tools.WntNode(f['id']))

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(33*cnt/nofn)

        # ADD LINKS
        cnt = 0
        for f in linklay.getFeatures():
            cnt += 1
            net.add_link(tools.WntLink(f['id'], f['start'], f['end']))

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
        feedback.pushInfo('='*40)
        msg = 'Processed: {} nodes and {} links'.format(nofn, nofl)
        feedback.pushInfo(msg)
        msg = 'Write: {} node degrees'.format(nofn)
        feedback.pushInfo(msg)
        msg = 'Degree min: {}. Degree max: {}'
        msg = msg.format(min(degrees.values()), max(degrees.values()))
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id}
