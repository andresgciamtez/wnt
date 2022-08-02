# -*- coding: utf-8 -*-

"""
/***************************************************************************
 WaterNetworTools
                                 A QGIS plugin
 Water Network Modelling Utilities
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2019-07-20
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
__date__ = '2019-07-20'
__copyright__ = '(C) 2019 by Andrés García Martínez'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
from .wnt_assign_demand import AssignDemandAlgorithm
from .wnt_classify import ClassifyAlgorithm
from .wnt_config_toolkit import ConfigToolkitAlgorithm
from .wnt_connect_by_distance import ConnectByDistanceAlgorithm
from .wnt_elevation_from_raster import ElevationFromRasterAlgorithm
from .wnt_elevation_from_tin import ElevationFromTINAlgorithm
from .wnt_epanet_from_network import EpanetFromNetworkAlgorithm
from .wnt_graph_from_network import GraphFromNetworkAlgorithm
from .wnt_hydrant_pairs import HydrantPairsAlgorithm
from .wnt_merge_networks import MergeNetworksAlgorithm
from .wnt_network_from_epanet import NetworkFromEpanetAlgorithm
from .wnt_network_from_landxml import NetworkFromLandXMLAlgorithm
from .wnt_network_from_lines import NetworkFromLinesAlgorithm
from .wnt_node_degrees import NodeDegreesAlgorithm
from .wnt_ppno_from_network import PpnoFromNetworkAlgorithm
from .wnt_results_from_epanet import ResultsFromEpanetAlgorithm
from .wnt_scn_from_demands import ScnFromDemandsAlgorithm
from .wnt_scn_from_pipe_properties import ScnFromPipePropertiesAlgorithm
from .wnt_split_lines_at_points import SplitLinesAtPointsAlgorithm
from .wnt_validate import ValidateAlgorithm
from .wnt_update_assignment import UpdateAssignmentAlgorithm

class WaterNetworkToolsProvider(QgsProcessingProvider):
    """Main class"""
    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(AssignDemandAlgorithm())
        self.addAlgorithm(ClassifyAlgorithm())
        self.addAlgorithm(ConfigToolkitAlgorithm())
        self.addAlgorithm(ConnectByDistanceAlgorithm())
        self.addAlgorithm(ElevationFromRasterAlgorithm())
        self.addAlgorithm(ElevationFromTINAlgorithm())
        self.addAlgorithm(EpanetFromNetworkAlgorithm())
        self.addAlgorithm(GraphFromNetworkAlgorithm())
        self.addAlgorithm(HydrantPairsAlgorithm())
        self.addAlgorithm(MergeNetworksAlgorithm())
        self.addAlgorithm(NetworkFromEpanetAlgorithm())
        self.addAlgorithm(NetworkFromLandXMLAlgorithm())
        self.addAlgorithm(NetworkFromLinesAlgorithm())
        self.addAlgorithm(NodeDegreesAlgorithm())
        self.addAlgorithm(PpnoFromNetworkAlgorithm())
        self.addAlgorithm(ResultsFromEpanetAlgorithm())
        self.addAlgorithm(ScnFromDemandsAlgorithm())
        self.addAlgorithm(ScnFromPipePropertiesAlgorithm())
        self.addAlgorithm(SplitLinesAtPointsAlgorithm())
        self.addAlgorithm(ValidateAlgorithm())
        self.addAlgorithm(UpdateAssignmentAlgorithm())

    def id(self):
        """
        Returns the unique provider id, used for identifying the provider. This
        string should be a unique, short, character only string, eg "qgis" or
        "gdal". This string should not be localised.
        """
        return 'wnt'

    def name(self):
        """
        Returns the provider name, which is used to describe the provider
        within the GUI.
        """
        return self.tr('Water Network Tools')

    def icon(self):
        """
        Should return a QIcon which is used for your provider inside
        the Processing toolbox.
        """
        return QgsProcessingProvider.icon(self)

    def longName(self):
        """
        Returns the a longer version of the provider name, which can include
        extra details such as version numbers. E.g. "Water Network Tools
        (version 2.2.1)". This string should be localised. The default
        implementation returns the same string as name().
        """
        return self.name()
