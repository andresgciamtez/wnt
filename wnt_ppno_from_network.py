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
                       QgsProcessingParameterEnum,
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
    ALGORITHM = 'ALGORITHM'
    TEMPLATE = 'TEMPLATE'
    OUTPUT = 'OUTPUT'
    ALGORITHMS = ['GD', 'DE', 'DA', 'NSGA2']

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
        return self.tr('Water Network tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'wnt'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        msg = 'Build a ppno ext file from nodes and links. \n'
        msg += 'In the node layer must be defined the pressure required. \n'
        msg += 'In the link layer must be defined the pipe series. \n'
        msg += 'Select the optimization algorithm, among: \n'
        msg += 'GD, DE, DA or NSGA-II \n'
        msg += 'https://github.com/andresgciamtez/ppno \n'
        msg += 'The template must contain the pipe series.'
        return self.tr(msg)

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
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ALGORITHM,
                self.tr('Algoritm'),
                options=self.ALGORITHMS,
                defaultValue=0
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
        algorithm = self.parameterAsEnum(parameters, self.ALGORITHM, context)

        # OUTPUT
        extfile = self.parameterAsFileOutput(
            parameters,
            self.OUTPUT,
            context
            )

        # TEMPLATE
        ppnof = htxt.Htxtf()
        ppnof.read(template)

        # TITLE SECTION
        msg = '; File generated automatically by Water Network Tools \n'
        ppnof.sections['TITLE'].append(msg)

        # INP SECTION
        ppnof.sections['INP'] = epanet

        # OPTIONS SECTION
        line = 'Algorithm ' + self.ALGORITHMS[algorithm]
        ppnof.sections['OPTIONS'].append(line)

        # PRESSURES SECTION
        pcnt = 0
        for feature in nodes.getFeatures():
            if feature[pfield]:
                print(feature[pfield])
                pcnt += 1
                line = feature['id']+' '*4 + str(feature[pfield])
                ppnof.sections['PRESSURES'].append(line)

        # SERIES SECTION
        scnt = 0
        for feature in links.getFeatures():
            if feature[sfield]:
                scnt += 1
                line = (feature['id']+' '*4 + str(feature[sfield]))
                ppnof.sections['PIPES'].append(line)

        # WRITE EXT FILE
        ppnof.write(extfile)

        # SHOW INFO
        msg = 'Nodes processed: {}.  Pipes: {}.'.format(pcnt, scnt)
        feedback.pushInfo(msg)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: extfile}
