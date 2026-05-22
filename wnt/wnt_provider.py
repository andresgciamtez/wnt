"""Processing provider for Water Network Tools."""

from qgis.core import QgsProcessingProvider
from .processes.wnt_assign_demand import AssignDemandAlgorithm
from .processes.wnt_classify import ClassifyAlgorithm
from .processes.wnt_config_toolkit import ConfigToolkitAlgorithm
from .processes.wnt_connect_by_distance import ConnectByDistanceAlgorithm
from .processes.wnt_elevation_from_raster import ElevationFromRasterAlgorithm
from .processes.wnt_elevation_from_tin import ElevationFromTINAlgorithm
from .processes.wnt_network_to_epanet import NetworkToEpanetAlgorithm
from .processes.wnt_network_to_xml import NetworkToXmlAlgorithm
from .processes.wnt_network_to_graph import NetworkToGraphAlgorithm
from .processes.wnt_hydrant_pairs import HydrantPairsAlgorithm
from .processes.wnt_network_from_xml import NetworkFromXmlAlgorithm
from .processes.wnt_merge_networks import MergeNetworksAlgorithm
from .processes.wnt_network_from_epanet import NetworkFromEpanetAlgorithm
from .processes.wnt_network_from_lines import NetworkFromLinesAlgorithm
from .processes.wnt_node_degrees import NodeDegreesAlgorithm
from .processes.wnt_network_to_ppno import NetworkToPpnoAlgorithm
from .processes.wnt_network_to_pipesizing import NetworkToPipesizingAlgorithm
from .processes.wnt_results_from_epanet import ResultsFromEpanetAlgorithm
from .processes.wnt_demand_to_epanet_scenario import DemandToEpanetScenarioAlgorithm
from .processes.wnt_pipe_propierties_to_epanet_scenario import PipePropiertiesToEpanetScenarioAlgorithm
from .processes.wnt_split_lines_at_points import SplitLinesAtPointsAlgorithm
from .processes.wnt_validate import ValidateAlgorithm
from .processes.wnt_update_assignment import UpdateAssignmentAlgorithm

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
        self.addAlgorithm(NetworkToEpanetAlgorithm())
        self.addAlgorithm(DemandToEpanetScenarioAlgorithm())
        self.addAlgorithm(PipePropiertiesToEpanetScenarioAlgorithm())
        self.addAlgorithm(NetworkToXmlAlgorithm())
        self.addAlgorithm(NetworkToGraphAlgorithm())
        self.addAlgorithm(HydrantPairsAlgorithm())
        self.addAlgorithm(NetworkFromXmlAlgorithm())
        self.addAlgorithm(MergeNetworksAlgorithm())
        self.addAlgorithm(NetworkFromEpanetAlgorithm())
        self.addAlgorithm(NetworkFromLinesAlgorithm())
        self.addAlgorithm(NodeDegreesAlgorithm())
        self.addAlgorithm(NetworkToPpnoAlgorithm())
        self.addAlgorithm(NetworkToPipesizingAlgorithm())
        self.addAlgorithm(ResultsFromEpanetAlgorithm())
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
        return 'Water Network Tools'

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
