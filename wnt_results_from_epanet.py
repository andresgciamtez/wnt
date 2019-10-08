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
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFile)
from . import toolkit as et

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
        msg = 'Import results from an epanet simulation.\n'
        msg += 'Imported results:\n'
        msg += '- Nodes\n'
        msg += '* time\n'
        msg += '* demand\n'
        msg += '* head\n'
        msg += '* pressure\n'
        msg += '- Links\n'
        msg += '* time\n'
        msg += '* flow\n'
        msg += '* velocity\n'
        msg += '* headloss\n'
        msg += '* status\n'
        msg += '* setting\n'
        msg += '* energy\n'
        return self.tr(msg)

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

        # OPEN TOOLKIT
        et.ENopen(epanetf, epanetf[:-4]+'.rpt')

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

        # GET AND WRITE RESULTS
        stepcount = 0
        nodecount = et.ENgetcount(et.EN_NODECOUNT)
        linkcount = et.ENgetcount(et.EN_LINKCOUNT)
        et.ENopenH()
        et.ENinitH(0)
        while True:
            # RUN A TIME SETP
            stepcount += 1
            time = et.ENrunH()
            for nodeix in range(nodecount):
                nodeid = str(et.ENgetnodeid(nodeix+1), encoding='utf-8')
                demand = et.ENgetnodevalue(nodeix+1, et.EN_DEMAND)
                head = et.ENgetnodevalue(nodeix+1, et.EN_HEAD)
                pressure = et.ENgetnodevalue(nodeix+1, et.EN_PRESSURE)
                f = QgsFeature()
                f.setAttributes([nodeid, time, demand, head, pressure])
                node_sink.addFeature(f)
            for linkix in range(linkcount):
                linkid = str(et.ENgetlinkid(linkix+1), encoding='utf-8')
                flow = et.ENgetlinkvalue(linkix+1, et.EN_FLOW)
                velocity = et.ENgetlinkvalue(linkix+1, et.EN_VELOCITY)
                headloss = et.ENgetlinkvalue(linkix+1, et.EN_HEADLOSS)
                if et.ENgetlinkvalue(linkix+1, et.EN_STATUS):
                    status = 'OPEN'
                else:
                    status = 'CLOSED'
                setting = et.ENgetlinkvalue(nodeix+1, et.EN_SETTING)
                energy = et.ENgetlinkvalue(nodeix+1, et.EN_ENERGY)
                f = QgsFeature()
                f.setAttributes([linkid, time, flow, velocity, headloss, \
                                 status, setting, energy])
                link_sink.addFeature(f)

            # END OF SIMULATON
            if et.ENnextH() == 0:
                break
        
        # CLOSE MODEL
        et.ENclose()
       
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
