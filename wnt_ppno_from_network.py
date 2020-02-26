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
                       QgsProcessingParameterField,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterFileDestination)
from . import htxt

class PpnoFromNetworkAlgorithm(QgsProcessingAlgorithm):
    """
    Build a ppno data file (.ext) from node and link data.
    """

    # DEFINE CONSTANTS
    NODE_INPUT = 'NODE_INPUT'
    PRESS_FIELD = 'PRESS_FIELD'
    LINK_INPUT = 'LINK_INPUT'
    SERIES_FIELD = 'SERIES_FIELD'
    EPANET = 'EPANET'
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
        return PpnoFromNetworkAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'ppno_from_network'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('ppno data file from network')

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
        return self.tr('''Generate a ppno .ext file to size a network.
        The required pressure must be defined in the layer of nodes.
        The series of pipes must be defined in the link layer.
        The .inp file must contain the epanet model to optimize.
        The ppno template (.ext) must contain the series of pipes.
        ====
        Genera un archivo ppno .ext para dimensionar una red.
        En la capa de nodos debe definirse la presión requerida.
        En la capa de links debe definirse la serie de diametros de tuberías.
        El archivo .inp debe contener el modelo de epanet para optimizar.
        La plantilla ppno (.ext) debe contener la serie de tuberías.

        --------
        Pressurized Pipe Network Optimizer \n'
        https://github.com/andresgciamtez/ppno'
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """

        # ADD THE INPUT SOURCES
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.NODE_INPUT,
                self.tr('Input node layer'),
                [QgsProcessing.TypeVectorPoint]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.PRESS_FIELD,
                self.tr('Required pressure Field'),
                'Required pressure',
                self.NODE_INPUT,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.LINK_INPUT,
                self.tr('Input link layer'),
                [QgsProcessing.TypeVectorLine]
                )
            )
        self.addParameter(
            QgsProcessingParameterField(
                self.SERIES_FIELD,
                self.tr('Pipe series field'),
                'Pipe series',
                self.LINK_INPUT,
                allowMultiple=False,
                optional=False
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.EPANET,
                self.tr('Epanet file'),
                extension='inp'
                )
            )
        self.addParameter(
            QgsProcessingParameterFile(
                self.TEMPLATE,
                self.tr('ppnp template file'),
                extension='ext'
                )
            )

        # ADD A FILE DESTINATION FOR RESULTS
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output ppno file'),
                fileFilter='*.ext'
                )
            )
    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodes = self.parameterAsSource(parameters, self.NODE_INPUT, context)
        pfield = self.parameterAsFields(parameters, self.PRESS_FIELD, context)
        pfield = pfield[0]
        links = self.parameterAsSource(parameters, self.LINK_INPUT, context)
        sfield = self.parameterAsFields(parameters, self.SERIES_FIELD, context)
        sfield = sfield[0]
        epanet = self.parameterAsFields(parameters, self.EPANET, context)
        template = self.parameterAsFile(parameters, self.TEMPLATE, context)

        # OUTPUT
        extfile = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # CHECK CRS
        if nodes.sourceCrs() != links.sourceCrs():
            msg = 'ERROR: Layers have different CRS!'
            feedback.reportError(msg)
            return {}

        # TEMPLATE
        ppnof = htxt.HeaderTxt()
        ppnof.read(template)

        # TITLE SECTION
        msg = '; File generated automatically by Water Network Tools \n'
        ppnof.sections['TITLE'].append(msg)

        # INP SECTION
        ppnof.sections['INP'] = epanet

        # PRESSURES SECTION
        ncnt = 0
        for feature in nodes.getFeatures():
            if feature[pfield]:
                print(feature[pfield])
                ncnt += 1
                line = feature['id']+' '*4 + str(feature[pfield])
                ppnof.sections['PRESSURES'].append(line)

        # PIPES SECTION
        pcnt = 0
        for feature in links.getFeatures():
            if feature[sfield]:
                pcnt += 1
                line = (feature['id']+' '*4 + str(feature[sfield]))
                ppnof.sections['PIPES'].append(line)

        # WRITE EXT FILE
        ppnof.write(extfile)

        # SHOW INFO
        feedback.pushInfo('='*40)
        msg = 'Nodes with min pressure especified: {}'.format(ncnt)
        feedback.pushInfo(msg)
        msg = 'Pipes to size: {}.'.format(pcnt)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)
        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: extfile}
