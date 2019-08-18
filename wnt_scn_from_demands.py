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
                       QgsProcessingParameterFileDestination)

class ScnFromDemandsAlgorithm(QgsProcessingAlgorithm):
    """
    Build an epanet scenary file from nodal demands.
    """

    # DEFINE CONSTANTS
    NODE_INPUT = 'NODE_INPUT'
    DEM_FIELD = 'DEM_FIELD'
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
        return ScnFromDemandsAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'scn_from_demand'

    def displayName(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('Scenario from nodal demands')

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Water Network Tools')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'wnt'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr("Make an epanet nodal demand scenario file.")

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
                self.DEM_FIELD,
                self.tr('Field containing demand'),
                'demand',
                self.NODE_INPUT,
                allowMultiple=True,
                optional=True
                )
            )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Epanet scenario file'),
                fileFilter='*.scn'
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        nodes = self.parameterAsSource(parameters, self.NODE_INPUT, context)
        defields = self.parameterAsFields(parameters, self.DEM_FIELD, context)

        # OUTPUT
        scnfn = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        file = open(scnfn, 'w')

        # IF NO FIELD WAS SELECTED RETURN {}
        if not defields:
            return {}

        # WRITE FILE
        cnt = 0
        scnfn = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        file = open(scnfn, 'w')
        msg = '; File generated automatically by Water Network Tools \n'
        file.write('msg')
        file.write('[DEMANDS] \n')
        file.write(';Node    Demand    Pattern \n')
        feedback.setProgress(5) # Update the progress bar

        for f in nodes.getFeatures():
            for field in defields:
                if f[field] and f['type'] == 'JUNCTION':
                    cnt += 1
                    line = '{}  {}  {} \n'.format(f['id'], f[field], field)
                    file.write(line)
        file.close()

        # SHOW INFO
        msg = 'Node demands added: {}, Categories: {}.'
        msg = msg.format(cnt, len(defields))
        feedback.pushInfo(msg)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT: scnfn}
