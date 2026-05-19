"""Import hydraulic results from EPANET toolkit runs."""

import configparser
import ctypes
import os
from pathlib import Path
from time import gmtime, strftime
from qgis.PyQt.QtCore import QMetaType
from qgis.core import (QgsFeature,
                       QgsField,
                       QgsFields,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFile)
from .base import WntProcessingAlgorithm
from .messages import error, finish, info, message, start


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

class ResultsFromEpanetAlgorithm(WntProcessingAlgorithm):
    """
    Import EPANET result from EPANET toolkit.
    """

    # DEFINE CONSTANTS
    INPUT = 'INPUT'
    OUTPUT_NODES = 'OUTPUT_NODES'
    OUTPUT_LINES = 'OUTPUT_LINES'


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
        return 'Results from EPANET'

    def group(self):
        """
        Returns the name of the group this algorithm belongs to.
        """
        return 'Import'

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to.
        """
        return 'import'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm.
        """
        return self.tr('''<p>Imports hydraulic results from an EPANET simulation.</p>
<ul>
<li>Node results: <code>time</code>, <code>demand</code>, <code>head</code>, <code>pressure</code>.</li>
<li>Link results: <code>time</code>, <code>flow</code>, <code>velocity</code>, <code>headloss</code>, <code>status</code>, <code>setting</code>, <code>energy</code>.</li>
</ul>
<p>Configure the EPANET toolkit library before running this algorithm.</p>
        ''')

    def initAlgorithm(self, config=None):
        """
         Define the inputs and outputs of the algorithm.
        """

        # ADD INPUT FILE
        self.addParameter(
            QgsProcessingParameterFile(
                self.INPUT,
                self.tr('EPANET file'),
                extension='inp'
            )
        )

        # ADD NODE AND LINK SINKS
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_NODES,
                self.tr('Node results')
            )
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT_LINES,
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
        newfields.append(QgsField("time", QMetaType.QTime))
        newfields.append(QgsField("id", QMetaType.QString, len=MAX_LABEL_LEN))
        newfields.append(QgsField("demand", QMetaType.Double))
        newfields.append(QgsField("head", QMetaType.Double))
        newfields.append(QgsField("pressure", QMetaType.Double))
        #newfields.append(QgsField("quality", QMetaType.Double))
        #newfields.append(QgsField("sourcemass", QMetaType.Double))
        (node_sink, nodes_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_NODES,
            context,
            newfields
            )

        # DEFINE LINK LAYER
        newfields = QgsFields()
        newfields.append(QgsField("time", QMetaType.QTime))
        newfields.append(QgsField("id", QMetaType.QString, len=MAX_LABEL_LEN))
        newfields.append(QgsField("flow", QMetaType.Double))
        newfields.append(QgsField("velocity", QMetaType.Double))
        newfields.append(QgsField("headloss", QMetaType.Double))
        newfields.append(QgsField("status", QMetaType.QString, len=6))
        newfields.append(QgsField("setting", QMetaType.Double))
        newfields.append(QgsField("energy", QMetaType.Double))
        (link_sink, links_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT_LINES,
            context,
            newfields
            )

        # SEND INFORMATION TO THE USER
        start(feedback, self.displayName())

        # LOAD EPANET LIB SELECTING OS AND PLATFORM
        try:
            config = configparser.ConfigParser()
            ini_file = Path(__file__).resolve().parents[1] / 'toolkit.ini'
            config.read(ini_file)
            lib_file = config['EPANET']['lib']
            info(feedback, "EPANET toolkit library", lib_file)
            if os.name in ['nt', 'dos']:
                info(feedback, "Operating system", os.name)
                epanet_lib = ctypes.windll.LoadLibrary(lib_file)
            else:
                info(feedback, "Operating system", os.name)
                epanet_lib = ctypes.cdll.LoadLibrary(lib_file)
        except:
            error(feedback, "Configure EPANET toolkit library")
            return {}

        # OPEN EPANET MODEL
        info(feedback, "Input file", epanet_file)
        report_file = epanet_file[:-4] + '.rpt'
        err = epanet_lib.ENopen(ctypes.c_char_p(epanet_file.encode()),
                                ctypes.c_char_p(report_file.encode())
                                )
        if err:
            error(feedback, f"EPANET toolkit error {err}")
            return {}

        # GET AND WRITE RESULTS
        step_count = 0
        count = ctypes.c_int()
        err = epanet_lib.ENgetcount(EN_NODECOUNT, ctypes.byref(count))
        if err:
            error(feedback, f"EPANET toolkit error {err}")
            return {}
        node_count = count.value
        err = epanet_lib.ENgetcount(EN_LINKCOUNT, ctypes.byref(count))
        if err:
            error(feedback, f"EPANET toolkit error {err}")
            return {}
        link_count = count.value
        err = epanet_lib.ENopenH()
        if err:
            error(feedback, f"EPANET toolkit error {err}")
            return {}
        err = epanet_lib.ENinitH(ctypes.c_int(NOSAVE))
        if err:
            error(feedback, f"EPANET toolkit error {err}")
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
                    error(feedback, f"EPANET toolkit error {err}")
                    return {}
                node_result = [time, id_.value.decode('utf-8')]
                for parameter in [EN_DEMAND, EN_HEAD, EN_PRESSURE]:
                    err = epanet_lib.ENgetnodevalue(index,
                                                    parameter,
                                                    ctypes.byref(variable)
                                                    )
                    if err:
                        error(feedback, f"EPANET toolkit error {err}")
                        return {}
                    node_result.append(variable.value)
                f = QgsFeature()
                f.setAttributes(node_result)
                node_sink.addFeature(f)

            # LINK RESULT
            for index in range(1, link_count + 1):
                err = epanet_lib.ENgetlinkid(index, ctypes.byref(id_))
                if err:
                    error(feedback, f"EPANET toolkit error {err}")
                    return {}
                link_result = [time, id_.value.decode('utf-8')]
                for parameter in [EN_FLOW, EN_VELOCITY, EN_HEADLOSS]:
                    err = epanet_lib.ENgetlinkvalue(index,
                                                    parameter,
                                                    ctypes.byref(variable)
                                                    )
                    if err:
                        error(feedback, f"EPANET toolkit error {err}")
                        return {}
                    link_result.append(variable.value)
                err = epanet_lib.ENgetlinkvalue(index,
                                                EN_STATUS,
                                                ctypes.byref(variable)
                                                )
                if err:
                    error(feedback, f"EPANET toolkit error {err}")
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
                        error(feedback, f"EPANET toolkit error {err}")
                        return {}
                    link_result.append(variable.value)
                f = QgsFeature()
                f.setAttributes(link_result)
                link_sink.addFeature(f)

            # END OF SIMULATON
            next_time = ctypes.c_long()
            err = epanet_lib.ENnextH(ctypes.byref(next_time))
            if err:
                error(feedback, f"EPANET toolkit error {err}")
                return {}
            if next_time.value == 0:
                break

        # CLOSE MODEL
        err = epanet_lib.ENclose()
        if err:
            error(feedback, f"EPANET toolkit error {err}")
            return {}
        # SHOW NODES AND LINKS PROCESSED
        message(feedback, "Results loaded successfully")
        info(feedback, "Hydraulic time steps", step_count)
        info(feedback, "Nodes", node_count)
        info(feedback, "Links", link_count)
        finish(feedback)

        # PROCCES CANCELED
        if feedback.isCanceled():
            return {}

        # OUTPUT
        return {self.OUTPUT_NODES: nodes_id, self.OUTPUT_LINES: links_id}

