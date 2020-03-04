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
                       QgsWkbTypes,
                       QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFeatureSource

                       )
from . import utils_core as tools

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
        return self.tr('Validate')

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
        return self.tr('''Analyse the network graph, verifying:
        - Orphan nodes
        - Duplicate nodes
        - Lines with undefined ends
        - Duplicate lines
        - Loops (lines with the same start and end node)
        
        The problems detected are stored in the field: *problems 
        
        ===
        
        Analiza el grafo de red, verificando:
        - Nodos huérfanos
        - Nodos duplicados
        - Líneas con extremos no definidos
        - Líneas duplicadas
        - Bucles (líneas con igual nodo de inicio y final)
        
        Los problemas detectados se almacenan en el campo: *problems.
        ''')

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
        net = tools.WntNetwork()

        # LOAD NODES
        ncnt = 0
        for f in nodelay.getFeatures():
            ncnt += 1
            net.add_node(tools.WntNode(f['id']))

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(25*ncnt/nodelay.featureCount())

        # lOAD LINKS
        lcnt = 0
        for f in linklay.getFeatures():
            lcnt += 1
            net.add_link(tools.WntLink(f['id'], f['start'], f['end']))

            # SHOW POROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(25+25*lcnt/linklay.featureCount())

        # VALIDATE
        problems = net.validate()

        # WRITE OUTPUT
        feedback.pushInfo('='*40)

        # WRITE NODE PROBLEMS
        ncnt = 0
        for f in nodelay.getFeatures():
            ncnt += 1
            msg = ''

            # ORPHAN NODE
            if f['id'] in problems['orphan nodes']:
                msg = 'Orphan.'

            # DUPLICATED NODE ID
            if f['id'] in problems['duplicate nodes']:
                msg += ' ' if msg else ''
                msg += 'Duplicated.'

            # ADD FEATURE
            attrib = f.attributes()
            attrib.extend([msg])
            f.setAttributes(attrib)
            node_sink.addFeature(f)

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(50+25*ncnt/nodelay.featureCount())

        # WRITE LINK PROBLEMS
        lcnt = 0
        for f in linklay.getFeatures():
            lcnt += 1
            msg = ''

            # UNDEFINED START OR END
            if f['id'] in problems['undefined node links']:
                msg = 'Undefined node links.'

            # DUPLICATED ID
            if f['id'] in problems['duplicate links']:
                msg += ' ' if msg else ''
                msg += 'Duplicate link.'

            # LOOP. START NODE ID = END NODE ID
            if f['id'] in problems['loops']:
                msg += ' ' if msg else ''
                msg += 'Loop.'

            # ADD FEATURE
            attrib = f.attributes()
            attrib.extend([msg])
            f.setAttributes(attrib)
            link_sink.addFeature(f)

            # SHOW PROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(75+25*lcnt/linklay.featureCount())

        # SHOW INFO
        msg = 'Analyzed: {} nodes and {} links'.format(ncnt, lcnt)
        feedback.pushInfo(msg)
        pcnt = 0
        for k, v in problems.items():
            pcnt += len(v)
            feedback.pushInfo("{} : {}".format(k, len(v)))

        if pcnt:
            msg = '{} problems detected! Check the network.'.format(pcnt)
        else:
            msg = "Network is valid."
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: node_id, self.LINK_OUTPUT: link_id}
