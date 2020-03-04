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
from . import utils_graph as gr

class ClassifyAlgorithm(QgsProcessingAlgorithm):
    """
    Build an epanet model file from node and link layers.
    """

    # DEFINE CONSTANTS
    LINK_INPUT = 'LINK_INPUT'
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
        return ClassifyAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'classify'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Classify')

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
        return self.tr('''Classify the network into branched and meshed areas.

        Two fields are added to the line layer:
        - 'graph_type': 'BRANCHED' for branched areas and 'MESHED' for meshes 
        areas.
        - 'sub': lists the subzones.
        
        Use this process to sectorize networks.
        ===
        Clasifica la red en zonas ramificadas y malladas.
        Se añaden dos campos a la capa de líneas:
        -  'graph_type': 'BRANCHED' para zonas ramificadas y 'MESHED' para las 
        malladas.
        - 'sub': enumera las subzonas.
        
        Use este proceso para sectorizar redes.
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT NETWORK LINKS
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINK_INPUT,
                self.tr('Network links layer input'),
                [QgsProcessing.TypeVectorLine]
                )
            )

        # ADD LINK FEATURE SINK
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINK_OUTPUT,
                self.tr('Subnetwork link layer')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        links = self.parameterAsSource(parameters, self.LINK_INPUT, context)

        # OUTPUT
        newfields = links.fields()
        newfields.append(QgsField("graph_type", QVariant.String))
        newfields.append(QgsField("sub", QVariant.Int))
        (link_sink, link_id) = self.parameterAsSink(
            parameters,
            self.LINK_OUTPUT,
            context,
            newfields,
            QgsWkbTypes.LineString,
            crs=links.sourceCrs()
            )

        # CREATE NETWORK
        netg = gr.Graph()

        # READ NETWORK
        nofl = links.featureCount()

        # LINKS
        cnt = 0
        for f in links.getFeatures():
            netg.add_edge(f['id'], f['start'], f['end'])

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(25*cnt/nofl)

        # GENERATE SUBNETWORKS
        classified = netg.classify()

        # WRITE LINK LAYER
        cnt = 0
        for f in links.getFeatures():
            print(classified[f['id']])
            cnt += 1
            attr = f.attributes()
            attr.extend(list(classified[f['id']][:]))
            f.setAttributes(attr)
            link_sink.addFeature(f)

            # SHOW PROGRESS
            if cnt % 100 == 0:
                feedback.setProgress(75+25*cnt/nofl)


        # SHOW INFO
        feedback.pushInfo('='*40)
        msg = 'Processed: {} links'.format(nofl)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.LINK_OUTPUT: link_id}
