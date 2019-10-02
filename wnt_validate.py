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
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource

                       )
from . import tools

class ValidateAlgorithm(QgsProcessingAlgorithm):
    """
    Validate a network.
    """

    # DEFINE CONSTANTS
    NODE_INPUT = 'NODE_INPUT'
    LINK_INPUT = 'LINK_INPUT'
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
        return ValidateAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'validate'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Validate network')

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
        msg = 'Analyse the network graph and generate a node '
        msg += 'layer with a field containing detected problems: \n'
        msg += '- the orphan nodes in the network \n'
        msg += '- the duplicated nodes in network \n'
        msg += '- undefined nodes in the network \n'
        msg += '- the duplicated links in network.'
        return self.tr(msg)

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODE_INPUT,
                self.tr('Input nodes layer'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINK_INPUT,
                self.tr('Input links layer'),
                [QgsProcessing.TypeVectorLine]
                )
            )

        # ADD NODE AND LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODE_OUTPUT,
                self.tr('Audited node layer')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINK_OUTPUT,
                self.tr('Audited Link layer')
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
        newfields.append(QgsField("problems", QVariant.String))
        (node_sink, node_id) = self.parameterAsSink(
            parameters,
            self.NODE_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.Point,
            nodelay.sourceCrs()
            )
        newfields = linklay.fields()
        newfields.append(QgsField("problems", QVariant.String))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.LINK_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString,
            linklay.sourceCrs()
            )

        # DEFINE NETWORK
        net = tools.Network()

        # LOAD NODES
        ncnt = 0
        for f in nodelay.getFeatures():
            ncnt += 1
            node = tools.Node(f['id'])
            net.nodes.append(node)

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(25*ncnt/nodelay.featureCount())

        # lOAD LINKS
        lcnt = 0
        for f in linklay.getFeatures():
            lcnt += 1
            link = tools.Link(f['id'], f['start'], f['end'])
            net.links.append(link)

            # SHOW POROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(25+25*lcnt/linklay.featureCount())

        # VALIDATE
        onodes, dnodes, unodes, dlinks, _ = net.validate()

        # WRITE OUTPUT
        g = QgsFeature()

        # WRITE NODE PROBLEMS
        ncnt = 0
        for f in nodelay.getFeatures():
            ncnt += 1
            problems = ''

            # ORPHAN NODE
            if f['id'] in onodes:
                problems = 'Orphan'

            # DUPLICATE NODE ID
            if f['id'] in dnodes:
                if problems:
                    problems += '. '
                problems += 'Duplicate ID'

            # ADD FEATURE
            attrib = f.attributes()
            attrib.extend([problems])
            g.setAttributes(attrib)
            node_sink.addFeature(g)

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(75+25*ncnt/nodelay.featureCount())

        # WRITE LINK PROBLEMS
        lcnt = 0
        loopcnt = 0
        for f in linklay.getFeatures():
            lcnt += 1
            problems = ''

            # NO DEFINED START OR END
            if f['start'] in unodes:
                problems = 'Undefined start node ID'
            if f['end'] in unodes:
                if problems:
                    problems += '. '
                problems += 'Undefined end node ID'

            # DUPLICATED ID
            if f['id'] in dlinks:
                if problems:
                    problems += '. '
                problems += 'Duplicate link ID'

            # START NODE ID = END NODE ID
            if f['start'] == f['end']:
                loopcnt += 1
                if problems:
                    problems += '. '
                problems += 'Start and end node IDs are the same'

            # ADD FEATURE
            attrib = f.attributes()
            attrib.extend([problems])
            g.setAttributes(attrib)
            link_sink.addFeature(g)

            # SHOW PROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(75+25*lcnt/linklay.featureCount())

        # SHOW INFO
        msg = 'Analyzed: {} nodes and {} links'.format(ncnt, lcnt)
        feedback.pushInfo(msg)
        msg = 'Orphan nodes: {}'.format(len(onodes))
        feedback.pushInfo(msg)
        msg = 'Duplicated nodes: {}'.format(len(dnodes))
        feedback.pushInfo(msg)
        msg = 'Undefined start or end links: {}'.format(len(unodes))
        feedback.pushInfo(msg)
        msg = 'Equal start and end links: {}'.format(loopcnt)
        feedback.pushInfo(msg)
        msg = 'Duplicated links: {}'.format(len(dlinks))
        feedback.pushInfo(msg)
        if onodes and dnodes and unodes and loopcnt and dlinks:
            msg = 'Problems detected! Check the network'
        else:
            msg = "Network is valid"
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id, self.LINK_OUTPUT: link_id}
