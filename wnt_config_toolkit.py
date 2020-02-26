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

import sys
import configparser
from PyQt5.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile)

class ConfigToolkitAlgorithm(QgsProcessingAlgorithm):
    """
    Set epanet lib path in tookit.ini file.
    """

    # DEFINE CONSTANTS
    INPUT = 'INPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        Create a instance and return a new copy of algorithm.
        """
        return ConfigToolkitAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'config_toolkit'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Configure epanet lib')

    def group(self):
        """
         Returns the name of the group this algorithm belongs to.
        """
        return self.tr('Import')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'import'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''Set the epanet lib path.
        
        Note: The path is store in the toolkit.ini file.
        
        Epanet lib can be download from: 
        https://www.epa.gov/water-research/epanet#tab-2 (only win 32)
        or
        https://github.com/andresgciamtez/entoolkit/tree/master/entoolkit/epanet
        ===
        Define la ruta de acceso a la biblioteca de epanet.

        Nota: La ruta de acceso se almacena en el archivo toolkit.ini.
        
        La biblioteca de epanet puede ser descargada desde:
        https://www.epa.gov/water-research/epanet#tab-2 (solo win 32)
        o
        https://github.com/andresgciamtez/entoolkit/tree/master/entoolkit/epanet
        ''')

    def initAlgorithm(self, config=None):
        """
        Define the inputs and outputs of the algorithm.
        """
        # ADD A FILE DESTINATION
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Epanet lib')
                )
            )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # OUTPUT
        libf = self.parameterAsFile(parameters, self.INPUT, context)
        inif = sys.path[0] + '/toolkit.ini'
        feedback.pushInfo(inif)
        config = configparser.ConfigParser()
        config.read(inif)
        config['EPANET']['lib'] = libf
        with open(inif, 'w') as configfile:
            config.write(configfile)

        # SHOW INFO
        feedback.pushInfo('='*40)
        msg = 'Epanet toolkit library: {}, saved. Restart QGIS.'.format(libf)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {}
