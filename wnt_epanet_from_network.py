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

from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from . import utils_core as tools

class EpanetFromNetworkAlgorithm(QgsProcessingAlgorithm):
    """
    Build an epanet model file from node and link layers.
    """

    # DEFINE CONSTANTS

    NODE_INPUT = 'NODE_INPUT'
    LINK_INPUT = 'LINK_INPUT'
    TEMPLATE = 'TEMPLATE'
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
        return EpanetFromNetworkAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'epanet_from_network'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Epanet file from network')

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Export')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'export'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''Generate an epanet inp file from a network and a
        epanet model template.
        The final epanet model contain the templated data adding,
        - in JUNCTIONS/RESERVOIRS/TANK: *id *elevation
        - in PIPES/PUMPS: *id *start *end
        - in VALVES; *id *start *end *type
        Note:
        - Coordinates and vertex are exported.
        - pipe diameter and roughness are ignored (add it like scenarios).
        
        Tip: It is possible extend the template model adding a the network.
        ===
        Genera un modelo epanet a partir de una red y una plantilla (.inp).
        El modelo final de epanet contendrá los datos de plantilla , añadiendo:
        - a JUNCTIONS/RESERVOIRS/TANK: *id *elevation
        - a PIPES/PUMPS: *id *start *end
        - a VALVES: *id *start *end *type
        Notas:
        - Se exportan la totalidad de la geometría.
        - Se ignora diámetros y rugosidades (añádalos mediante escenarios).

        Consejo: Puede ampliar el modelo de la plantilla con la nueva red.
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
        self.addParameter(
            QgsProcessingParameterFile(
                self.TEMPLATE,
                self.tr('Epanet template file'),
                extension='inp'
                )
            )

        # ADD A FILE DESTINATION
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Epanet model file'),
                fileFilter='*.inp'
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """
        # INPUT
        nodes = self.parameterAsSource(parameters, self.NODE_INPUT, context)
        links = self.parameterAsSource(parameters, self.LINK_INPUT, context)
        template = self.parameterAsFile(parameters, self.TEMPLATE, context)

        # CHECK CRS
        crs = nodes.sourceCrs()
        if crs == links.sourceCrs():

            # SEND INFORMATION TO THE USER
            feedback.pushInfo('='*40)
            feedback.pushInfo('CRS is {}'.format(crs.authid()))
        else:
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

        # OUTPUT
        epanet = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # BUILD NETWORK
        newnet = tools.WntNetwork()

        # NODES
        ncnt = 0
        for f in nodes.getFeatures():
            ncnt += 1
            newnode = tools.WntNode(f['id'])
            newnode.from_wkt(f.geometry().asWkt())
            newnode.set_type(f['type'])
            newnode.set_elevation(f['elevation'])
            newnet.add_node(newnode)

            # SHOW PROGRESS
            if ncnt % 100 == 0:
                feedback.setProgress(50*ncnt/nodes.featureCount())

        # LINKS
        lcnt = 0
        for f in links.getFeatures():
            lcnt += 1
            newlink = tools.WntLink(f['id'], f['start'], f['end'])
            newlink.from_wkt(f.geometry().asWkt())
            newlink.epanet['length'] = f['length']
            newlink.set_type(f['type'])
            newnet.add_link(newlink)

            # SHOW POROGRESS
            if lcnt % 100 == 0:
                feedback.setProgress(50+50*lcnt/links.featureCount())

        # WRITE NET
        newnet.to_epanet(epanet, template)
        epanet = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # SHOW INFO
        msg = 'Model contains: {} nodes and {} links.'.format(ncnt, lcnt)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: epanet}
