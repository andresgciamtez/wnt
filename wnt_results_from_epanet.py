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

import configparser
import ctypes
import sys
import os
from configparser import ConfigParser
from time import gmtime, strftime
from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFile)


# EPANET TOOLKIT CONSTANTS
EN_NODECOUNT = 0
EN_LINKCOUNT = 2
EN_DEMAND = 9
EN_HEAD = 10
EN_PRESSURE = 11
EN_FLOW = 8
EN_VELOCITY = 9
EN_HEADLOSS = 10
EN_STATUS = 11
EN_SETTING = 12
EN_ENERGY = 13
MAX_LABEL_LEN = 16
NOSAVE = 0

class ResultsFromEpanetAlgorithm(QgsProcessingAlgorithm):
    """
    Import epanet result from epanet toolkit.
    """

    # DEFINE CONSTANTS
    INPUT = 'INPUT'
    NODE_OUTPUT = 'NODE_OUTPUT'
    LINK_OUTPUT = 'LINK_OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        """
        createInstance must return a new copy of algorithm.
        """
        return ResultsFromEpanetAlgorithm()

    def name(self):
        """
        Returns the unique algorithm name, used for identifying the algorithm.
        """
        return 'results_from_epanet'

    def displayName(self):
        """
        Returns the translated algorithm name.
        """
        return self.tr('Results from epanet')

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
        return self.tr('''Import results from an epanet simulation.
        Imported data:
        Nodes: *time *demand *head *pressure
        Links: *time *flow *velocity *headloss *status *setting *energy
        
        Note: It is necessary to configure the access to epanet lib. 
        Use Import/Configure epanet toolkit libary*
        
        ===
        
        Importa los resultados de una simulación en epanet.
        Datos importados:
        Nodos: *time *demand *head *pressure
        Líneas: *time *flow *velocity *headloss *status *setting *energy
        
        Nota: Es necesario configurar el acceso a epanet de forma previa.
        Use Import/Configure epanet toolkit libary
        ''')

    def initAlgorithm(self, config=None):
        """
         Define the inputs and outputs of the algorithm.
        """

        # ADD INPUT FILE
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('Epanet file'),
                extension='inp'
            )
        )

        # ADD NODE AND LINK SINKS
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NODE_OUTPUT,
                self.tr('Node results')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.LINK_OUTPUT,
                self.tr('Link results'),
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        RUN PROCESS
        """

        # INPUT
        epanet_file = self.parameterAsFile(parameters, self.INPUT, context)

        # DEFINE NODE LAYER
        newfields = QgsFields()
        newfields.append(QgsField("time", QVariant.Time))
        newfields.append(QgsField("id", QVariant.Char, len=MAX_LABEL_LEN))
        newfields.append(QgsField("demand", QVariant.Double))
        newfields.append(QgsField("head", QVariant.Double))
        newfields.append(QgsField("pressure", QVariant.Double))
        #newfields.append(QgsField("quality", QVariant.Double))
        #newfields.append(QgsField("sourcemass", QVariant.Double))
        (node_sink, nodes_id) = self.parameterAsSink(
            parameters,
            self.NODE_OUTPUT,
            context,
            newfields
            )

        # DEFINE LINK LAYER
        newfields = QgsFields()
        newfields.append(QgsField("time", QVariant.Time))
        newfields.append(QgsField("id", QVariant.Char, len=MAX_LABEL_LEN))
        newfields.append(QgsField("flow", QVariant.Double))
        newfields.append(QgsField("velocity", QVariant.Double))
        newfields.append(QgsField("headloss", QVariant.Double))
        newfields.append(QgsField("status", QVariant.Char, len=6))
        newfields.append(QgsField("setting", QVariant.Double))
        newfields.append(QgsField("energy", QVariant.Double))
        (link_sink, links_id) = self.parameterAsSink(
            parameters,
            self.LINK_OUTPUT,
            context,
            newfields
            )

        # SEND INFORMATION TO THE USER
        feedback.pushInfo('='*40)

        # LOAD EPANET LIB SELECTING OS AND PLATFORM
        try:
            config = configparser.ConfigParser()
            ini_file = sys.path[0] + '/toolkit.ini'
            config.read(ini_file)
            lib_file = config['EPANET']['lib']
            feedback.pushInfo(f'Epanet library file: {lib_file}')
            if os.name in ['nt', 'dos']:
                feedback.pushInfo(f'OS: {os.name}')
                epanet_lib = ctypes.windll.LoadLibrary(lib_file)
            else:
                feedback.pushInfo('Non-windows OS.')
                epanet_lib = ctypes.cdll.LoadLibrary(lib_file)
        except:
            feedback.reportError('ERROR: Configure epanet library!')
            return {}

        # OPEN EPANET MODEL
        feedback.pushInfo(f'Processing: {epanet_file}')
        report_file = epanet_file[:-4] + '.rpt'
        err = epanet_lib.ENopen(ctypes.c_char_p(epanet_file.encode()),
                                ctypes.c_char_p(report_file.encode())
                                )
        if err:
            feedback.reportError('Epanet Toolkit error: {err}!')
            return {}

        # GET AND WRITE RESULTS
        step_count = 0
        count = ctypes.c_int()
        err = epanet_lib.ENgetcount(EN_NODECOUNT, ctypes.byref(count))
        if err:
            feedback.reportError('Epanet Toolkit error: {err}!')
            return {}
        node_count = count.value
        err = epanet_lib.ENgetcount(EN_LINKCOUNT, ctypes.byref(count))
        if err:
            feedback.reportError('Epanet Toolkit error: {err}!')
            return {}
        link_count = count.value
        err = epanet_lib.ENopenH()
        if err:
            feedback.reportError('Epanet Toolkit error: {err}!')
            return {}
        err = epanet_lib.ENinitH(ctypes.c_int(NOSAVE))
        if err:
            feedback.reportError('Epanet Toolkit error: {err}!')
            return {}
        while True:

            # RUN A TIME SETP
            step_count += 1
            current_time = ctypes.c_long()
            err = epanet_lib.ENrunH(ctypes.byref(current_time))
            time = strftime('%H:%M:%S', gmtime(current_time.value))
            id_ = ctypes.create_string_buffer(MAX_LABEL_LEN)
            variable = ctypes.c_float()

            # NODE RESULT
            for index in range(1, node_count + 1):
                err = epanet_lib.ENgetnodeid(index, ctypes.byref(id_))
                if err:
                    feedback.reportError('Epanet Toolkit error: {err}!')
                    return {}
                node_result = [time, str(id_, encoding='utf-8')]
                for parameter in [EN_DEMAND, EN_HEAD, EN_PRESSURE]:
                    err = epanet_lib.ENgetnodevalue(index,
                                                    parameter,
                                                    ctypes.byref(variable)
                                                    )
                    if err:
                        feedback.reportError('Epanet Toolkit error: {err}!')
                        return {}
                    node_result.append(variable.value)
                f = QgsFeature()
                f.setAttributes(node_result)
                node_sink.addFeature(f)

            # LINK RESULT
            for index in range(1, link_count + 1):
                err = epanet_lib.ENgetlinkid(index, ctypes.byref(id_))
                if err:
                    feedback.reportError('Epanet Toolkit error: {err}!')
                    return {}
                link_result = [time, str(id_, encoding='utf-8')]
                for parameter in [EN_FLOW, EN_VELOCITY, EN_HEADLOSS]:
                    err = epanet_lib.ENgetlinkvalue(index,
                                                    parameter,
                                                    ctypes.byref(variable)
                                                    )
                    link_result.append(variable.value)
                err = epanet_lib.ENgetlinkvalue(index,
                                                EN_SETTING,
                                                ctypes.byref(variable)
                                                )
                if err:
                    feedback.reportError('Epanet Toolkit error: {err}!')
                    return {}
                if variable.value:
                    link_result.append('OPEN')
                else:
                    link_result.append('CLOSED')
                for parameter in [EN_SETTING, EN_ENERGY]:
                    err = epanet_lib.ENgetlinkvalue(index,
                                                    parameter,
                                                    ctypes.byref(variable)
                                                    )
                    if err:
                        feedback.reportError('Epanet Toolkit error: {err}!')
                        return {}
                    link_result.append(variable.value)
                f = QgsFeature()
                f.setAttributes(link_result)
                link_sink.addFeature(f)

            # END OF SIMULATON
            next_time = ctypes.c_long()
            err = epanet_lib.ENnextH(ctypes.byref(next_time))
            if err:
                feedback.reportError('Epanet Toolkit error: {err}!')
                return {}
            if next_time.value == 0:
                break

        # CLOSE MODEL
        err = epanet_lib.ENclose()
        if err:
            feedback.reportError('Epanet Toolkit error: {err}!')
            return {}
        # SHOW NODES AND LINKS PROCESSED
        msg = 'Results loaded successfully.'
        feedback.pushInfo(msg)
        msg = 'Hydraulic time steps #: {}'.format(step_count)
        feedback.pushInfo(msg)
        msg = 'Node #: {}'.format(node_count)
        feedback.pushInfo(msg)
        msg = 'Link #: {}'.format( link_count)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: nodes_id, self.LINK_OUTPUT: links_id}
