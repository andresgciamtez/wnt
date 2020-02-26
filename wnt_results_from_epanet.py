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

import ctypes
import sys
from PyQt5.QtCore import QCoreApplication, QVariant
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFile)
from configparser import ConfigParser

class ENToolkit:
    EN_DEMAND = 9
    EN_HEAD = 10
    EN_PRESSURE = 11
    EN_FLOW = 8
    EN_VELOCITY = 9
    EN_HEADLOSS = 10
    EN_STATUS = 11
    EN_SETTING = 12
    EN_ENERGY = 13
    EN_NODECOUNT = 0
    EN_LINKCOUNT = 2
    MAX_LABEL_LEN = 15
    _lib = None

    def __init__(self):
        try:
            config = ConfigParser()
            inif = sys.path[0] + '/toolkit.ini'
            config.read(inif)
            file = config['EPANET']['lib']
            ENToolkit._lib = ctypes.windll.LoadLibrary(file)
        except:
            raise FileNotFoundError('Error loading library. Check toolkit.ini.')

    def ENopen(self, inpfn, rptfn='', binfn=''):
        return ENToolkit._lib.ENopen(ctypes.c_char_p(inpfn.encode()),
                                     ctypes.c_char_p(rptfn.encode()),
                                     ctypes.c_char_p(binfn.encode())
                                     )

    def ENopenH(self):
        return ENToolkit._lib.ENopenH()

    def ENinitH(self, flag=None):
        return ENToolkit._lib.ENinitH(flag)

    def ENrunH(self):
        t = ctypes.c_long()
        return ENToolkit._lib.ENrunH(ctypes.byref(t)), t.value

    def ENgetcount(self, countcode):
        j = ctypes.c_int()
        return ENToolkit._lib.ENgetcount(countcode, ctypes.byref(j)), j.value

    def ENgetnodeid(self, index):
        label = ctypes.create_string_buffer(ENToolkit.MAX_LABEL_LEN)
        return ENToolkit._lib.ENgetnodeid(index, ctypes.byref(label)), label.value

    def ENgetnodevalue(self, index, paramcode):
        j = ctypes.c_float()
        return ENToolkit._lib.ENgetnodevalue(index, paramcode, ctypes.byref(j)), j.value

    def ENgetlinkid(self, index):
        label = ctypes.create_string_buffer(ENToolkit.MAX_LABEL_LEN)
        return ENToolkit._lib.ENgetlinkid(index, ctypes.byref(label)), label.value

    def ENgetlinkvalue(self, index, paramcode):
        j = ctypes.c_float()
        return ENToolkit._lib.ENgetlinkvalue(index, paramcode, ctypes.byref(j)), j.value

    def ENnextH(self):
        deltat = ctypes.c_long()
        return ENToolkit._lib.ENnextH(ctypes.byref(deltat)), deltat.value

    def ENclose(self):
        return ENToolkit._lib.ENclose()


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
        - Nodes: * time * demand * head * pressure
        - Links: * time * flow * velocity * headloss * status * setting
        * energy
        
        Tip: It is necessary configure the access to epanet. 
        Import/Configure epanet toolkit libary
        ===
        Importa los resultados de una simulación en epanet.
        Datos importados:
        - Nodos: * time * demand * head * pressure
        - Líneas: * time * flow * velocity * headloss * status * setting
        * energy
        
        Nota: Es necesario configurar el acceso a epanet de forma previa.
        Import/Configure epanet toolkit libary
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
        epanetf = self.parameterAsFile(parameters, self.INPUT, context)

        # DEFINE NODE LAYER
        newfields = QgsFields()
        newfields.append(QgsField("id", QVariant.Char))
        newfields.append(QgsField("time", QVariant.Time))
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
        newfields.append(QgsField("id", QVariant.Char))
        newfields.append(QgsField("time", QVariant.Time))
        newfields.append(QgsField("flow", QVariant.Double))
        newfields.append(QgsField("velocity", QVariant.Double))
        newfields.append(QgsField("headloss", QVariant.Double))
        newfields.append(QgsField("status", QVariant.String))
        newfields.append(QgsField("setting", QVariant.Double))
        newfields.append(QgsField("energy", QVariant.Double))
        (link_sink, links_id) = self.parameterAsSink(
            parameters,
            self.LINK_OUTPUT,
            context,
            newfields
            )

        # OPEN TOOLKIT
        sim = ENToolkit()
        sim.ENopen(epanetf, epanetf[:-4]+'.rpt')

        # GET AND WRITE RESULTS
        stepcount = 0
        err, nodecount = sim.ENgetcount(sim.EN_NODECOUNT)
        err, linkcount = sim.ENgetcount(sim.EN_LINKCOUNT)
        sim.ENopenH()
        sim.ENinitH(0)
        while True:
            # RUN A TIME SETP
            stepcount += 1
            err, time = sim.ENrunH()
            for nodeix in range(1, nodecount + 1):
                nodeid = str(sim.ENgetnodeid(nodeix)[1], encoding='utf-8')
                err, demand = sim.ENgetnodevalue(nodeix, sim.EN_DEMAND)
                err, head = sim.ENgetnodevalue(nodeix, sim.EN_HEAD)
                err, pressure = sim.ENgetnodevalue(nodeix, sim.EN_PRESSURE)
                f = QgsFeature()
                f.setAttributes([nodeid, time, demand, head, pressure])
                node_sink.addFeature(f)
            for linkix in range(1, linkcount + 1):
                linkid = str(sim.ENgetlinkid(linkix)[1], encoding='utf-8')
                err, flow = sim.ENgetlinkvalue(linkix, sim.EN_FLOW)
                err, velocity = sim.ENgetlinkvalue(linkix, sim.EN_VELOCITY)
                err, headloss = sim.ENgetlinkvalue(linkix, sim.EN_HEADLOSS)
                if sim.ENgetlinkvalue(linkix, sim.EN_STATUS)[1]:
                    status = 'OPEN'
                else:
                    status = 'CLOSED'
                setting = err, sim.ENgetlinkvalue(nodeix+1, sim.EN_SETTING)
                energy = err, sim.ENgetlinkvalue(nodeix+1, sim.EN_ENERGY)
                f = QgsFeature()
                f.setAttributes([linkid, time, flow, velocity, headloss, \
                                 status, setting, energy])
                link_sink.addFeature(f)

            # END OF SIMULATON
            if sim.ENnextH()[1] == 0:
                break

        # CLOSE MODEL
        sim.ENclose()

        # SHOW NODES AND LINKS PROCESSED
        feedback.pushInfo('='*40)
        msg = 'Number of hydraulic time steps: {}'.format(stepcount)
        feedback.pushInfo(msg)
        msg = 'Read results: {} nodes and {} link'.format(nodecount, linkcount)
        feedback.pushInfo(msg)
        feedback.pushInfo('='*40)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.NODE_OUTPUT: nodes_id, self.LINK_OUTPUT: links_id}
