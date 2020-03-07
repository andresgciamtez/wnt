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
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFileDestination
                      )
from . import utils_core as tools

class GraphFromNetworkAlgorithm(QgsProcessingAlgorithm):
    """
    Set the node elevation from a DEM in raster format.
    """

    # DEFINE CONSTANTS
    NODE_INPUT = 'NODE_INPUT'
    LINK_INPUT = 'LINK_INPUT'
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
        return GraphFromNetworkAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'graph_from_network'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Graph from network')

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
        Returns a localised short help string for the algorithm.
        """
        return self.tr('''Generate a graph from the network.

        Format: Trivial Chart Format, TGF
        
        Suggestion: yEd support TFG format.
        ===
        Generar un grafo de la red.

        Formato: Formato de gráfico trivial, TGF.
        
        Sugerencia: yEd admite el formato TFG. 
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT SOURCES
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODE_INPUT,
                self.tr('Input node vector layer'),
                types=[QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINK_INPUT,
                self.tr('Input link vector layer'),
                types=[QgsProcessing.TypeVectorLine]
                )
            )

        #ADD THE OUTPUT SINK
        # ADD A FILE DESTINATION
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Trivial Graph Format file'),
                fileFilter='*.tgf'
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodes = self.parameterAsSource(parameters, self.NODE_INPUT, context)
        links = self.parameterAsSource(parameters, self.LINK_INPUT, context)

        # OUTPUT
        graphfile = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        # GENERATE NETWORK
        net = tools.WntNetwork()
        for f in nodes.getFeatures():
            net.add_node(tools.WntNode(f['id']))
        for f in links.getFeatures():
            net.add_link(tools.WntLink(f['id'], f['start'], f['end']))

        # GENERATE GRAPH
        net.to_tgf(graphfile)

        # SHOW INFO
        feedback.pushInfo('='*40)
        msg = 'Graph generated. Nodes: {}. Edges: {}.'
        msg = msg.format(nodes.featureCount(), links.featureCount())
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: graphfile}
