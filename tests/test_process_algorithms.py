"""Execution tests for selected Processing algorithms."""

import textwrap

import pytest
from qgis.core import QgsGeometry, QgsLineString, QgsMultiLineString, QgsPoint, QgsPointXY

from wnt.processes import messages
from wnt.processes.wnt_assign_demand import AssignDemandAlgorithm
from wnt.processes.wnt_config_toolkit import ConfigToolkitAlgorithm
from wnt.processes.wnt_graph_from_network import GraphFromNetworkAlgorithm
from wnt.processes.wnt_classify import ClassifyAlgorithm
from wnt.processes.wnt_connect_by_distance import ConnectByDistanceAlgorithm
from wnt.processes.wnt_elevation_from_raster import ElevationFromRasterAlgorithm
from wnt.processes.wnt_elevation_from_tin import ElevationFromTINAlgorithm
from wnt.processes.wnt_epanet_from_network import EpanetFromNetworkAlgorithm
from wnt.processes.wnt_hydrant_pairs import HydrantPairsAlgorithm
from wnt.processes.wnt_merge_networks import MergeNetworksAlgorithm, aligned_feature
from wnt.processes.wnt_network_from_epanet import NetworkFromEpanetAlgorithm
from wnt.processes.wnt_network_from_landxml import NetworkFromLandXMLAlgorithm
from wnt.processes.wnt_network_from_lines import NetworkFromLinesAlgorithm
from wnt.processes.wnt_node_degrees import NodeDegreesAlgorithm
from wnt.processes.wnt_ppno_from_network import PpnoFromNetworkAlgorithm
from wnt.processes.wnt_results_from_epanet import ResultsFromEpanetAlgorithm
from wnt.processes.wnt_scn_from_demands import ScnFromDemandsAlgorithm
from wnt.processes.wnt_scn_from_pipe_properties import ScnFromPipePropertiesAlgorithm
from wnt.processes.wnt_split_lines_at_points import SplitLinesAtPointsAlgorithm
from wnt.processes.wnt_update_assignment import UpdateAssignmentAlgorithm
from wnt.processes.wnt_validate import ValidateAlgorithm
from wnt.utils.utils_epanet_api import (
    constants_for_version,
    EpanetConfigurationError,
    EpanetToolkit,
    ToolkitInfo,
)

from .utilities import get_qgis_app


QGIS_APP = get_qgis_app()


pytestmark = pytest.mark.qgis


class FakeCrs:
    def __init__(self, authid="EPSG:25830"):
        self._authid = authid

    def authid(self):
        return self._authid

    def __eq__(self, other):
        return isinstance(other, FakeCrs) and self._authid == other._authid


class FakeFields(list):
    def lookupField(self, name):
        for index, field in enumerate(self):
            if getattr(field, "name", lambda: None)() == name:
                return index
        return -1

    def names(self):
        return [field.name() for field in self]


class FakeNamedField:
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name


class FakeFeature:
    def __init__(self, attrs, geometry=None, fid=0):
        self._attrs = dict(attrs)
        self._attributes = list(attrs.values())
        self._geometry = geometry
        self._fid = fid

    def __getitem__(self, key):
        return self._attrs[key]

    def __setitem__(self, key, value):
        self._attrs[key] = value

    def attributes(self):
        return list(self._attributes)

    def setAttributes(self, attrs):
        self._attributes = list(attrs)

    def geometry(self):
        return self._geometry

    def setGeometry(self, geometry):
        self._geometry = geometry

    def id(self):
        return self._fid

    def fields(self):
        return FakeFields(FakeNamedField(name) for name in self._attrs)


class FakeSource:
    def __init__(self, features, fields=None, crs=None, wkb_type=1):
        self._features = features
        self._fields = fields or FakeFields()
        self._crs = crs or FakeCrs()
        self._wkb_type = wkb_type

    def getFeatures(self, *args):
        return iter(self._features)

    def featureCount(self):
        return len(self._features)

    def fields(self):
        return FakeFields(self._fields)

    def sourceCrs(self):
        return self._crs

    def wkbType(self):
        return self._wkb_type


class FakeSink:
    def __init__(self):
        self.features = []

    def addFeature(self, feature, *args):
        self.features.append(feature)

    def addFeatures(self, features, *args):
        self.features.extend(features)


class FakeLayerDetails:
    def __init__(self):
        self.name = None


class FakeProcessingContext:
    def __init__(self):
        self.layer_details = {}

    def layerToLoadOnCompletionDetails(self, layer_id):
        return self.layer_details.setdefault(layer_id, FakeLayerDetails())


class FakeOutputFeature:
    def __init__(self, *args):
        self.geometry_value = None
        self.attributes_value = None
        self._attrs = {}

    def setGeometry(self, geometry):
        self.geometry_value = geometry

    def setAttributes(self, attrs):
        self.attributes_value = list(attrs)

    def __getitem__(self, key):
        return self._attrs[key]

    def __setitem__(self, key, value):
        self._attrs[key] = value


class FakeFeedback:
    def __init__(self, canceled=False):
        self.canceled = canceled
        self.info = []
        self.errors = []
        self.progress = []

    def pushInfo(self, text):
        self.info.append(text)

    def reportError(self, text):
        self.errors.append(text)

    def setProgress(self, value):
        self.progress.append(value)

    def isCanceled(self):
        return self.canceled


def bind_common_parameters(monkeypatch, algorithm, sources=None, fields=None, files=None):
    sources = sources or {}
    fields = fields or {}
    files = files or {}
    numbers = {}
    sinks = {}

    monkeypatch.setattr(
        algorithm,
        "parameterAsSource",
        lambda parameters, name, context: sources[name],
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsRasterLayer",
        lambda parameters, name, context: sources[name],
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsFields",
        lambda parameters, name, context: fields[name]
        if isinstance(fields[name], list)
        else [fields[name]],
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsString",
        lambda parameters, name, context: fields[name],
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsInt",
        lambda parameters, name, context: fields[name],
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsDouble",
        lambda parameters, name, context: fields[name],
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsBool",
        lambda parameters, name, context: fields.get(name, False),
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsFile",
        lambda parameters, name, context: str(files[name]),
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsFileOutput",
        lambda parameters, name, context: str(files[name]),
    )
    monkeypatch.setattr(
        algorithm,
        "parameterAsCrs",
        lambda parameters, name, context: fields[name],
    )

    def parameter_as_sink(parameters, name, context, *args, **kwargs):
        sink = FakeSink()
        sinks[name] = sink
        return sink, f"{name}_id"

    monkeypatch.setattr(algorithm, "parameterAsSink", parameter_as_sink)
    return sinks


class FakePoint:
    def __init__(self, x, y, z=None):
        self._x = x
        self._y = y
        self._z = z

    def x(self):
        return self._x

    def y(self):
        return self._y

    def z(self):
        return self._z if self._z is not None else float("nan")

    def distance(self, other):
        return ((self._x - other.x()) ** 2 + (self._y - other.y()) ** 2) ** 0.5


class FakeLineGeometry:
    def __init__(self, distance):
        self._distance = distance

    def length(self):
        return self._distance


class FakeGeometry:
    def __init__(self, x, y, wkt=None, polyline=None, multipolyline=None):
        self._point = FakePoint(x, y)
        self._wkt = wkt
        self._polyline = polyline
        self._multipolyline = multipolyline

    def asPoint(self):
        return self._point

    def asPolyline(self):
        return self._polyline or [self._point]

    def asMultiPolyline(self):
        return self._multipolyline or []

    def shortestLine(self, other):
        return FakeLineGeometry(self._point.distance(other.asPoint()))

    def distance(self, other):
        return self._point.distance(other.asPoint())

    def asWkt(self):
        return self._wkt or f"Point({self._point.x()} {self._point.y()})"


class FakeRasterProvider:
    def sample(self, point, band):
        if point.x() < 0:
            return None, False
        return point.x() + point.y(), True


class FakeRaster:
    def __init__(self, crs=None):
        self._crs = crs or FakeCrs()

    def crs(self):
        return self._crs

    def dataProvider(self):
        return FakeRasterProvider()


class FakeSpatialIndex:
    def __init__(self, features):
        self._features = list(features)

    def nearestNeighbor(self, point, count):
        ordered = sorted(
            self._features,
            key=lambda feature: point.distance(feature.geometry().asPoint()),
        )
        return [feature.id() for feature in ordered[:count]]


class FakeQgsGeometry:
    @staticmethod
    def fromPolyline(polyline):
        return FakeGeometry(0, 0, polyline=polyline)

    @staticmethod
    def fromPolylineXY(polyline):
        return FakeGeometry(0, 0, polyline=polyline)

    @staticmethod
    def fromPointXY(point):
        return FakeGeometry(point.x(), point.y())


def test_messages_cover_all_branches():
    feedback = FakeFeedback()

    messages.start(feedback, "Title")
    messages.finish(feedback)
    messages.info(feedback, "A", 1)
    messages.message(feedback, "plain")
    messages.crs(feedback, FakeCrs("EPSG:4326"))
    messages.crs(feedback, "")
    messages.warning(feedback, "careful")
    messages.error(feedback, "broken")

    assert "Process: Title" in feedback.info
    assert "CRS: EPSG:4326" in feedback.info
    assert "WARNING: CRS is not set" in feedback.info
    assert feedback.errors == ["ERROR: broken"]


def test_graph_from_network_writes_tgf_and_handles_cancel(monkeypatch, tmp_path):
    algorithm = GraphFromNetworkAlgorithm()
    nodes = FakeSource([FakeFeature({"id": "N1"}), FakeFeature({"id": "N2"})])
    links = FakeSource([FakeFeature({"id": "L1", "start": "N1", "end": "N2"})])
    output = tmp_path / "network.tgf"
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_LINES: links},
        files={algorithm.OUTPUT: output},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT: str(output)}
    assert "0 N1" in output.read_text(encoding="utf-8")

    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def test_node_degrees_writes_degree_field(monkeypatch):
    algorithm = NodeDegreesAlgorithm()
    nodes = FakeSource([FakeFeature({"id": "N1"}), FakeFeature({"id": "N2"})])
    links = FakeSource([FakeFeature({"id": "L1", "start": "N1", "end": "N2"})])
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_LINES: links},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id"}
    assert [feature.attributes()[-1] for feature in sinks[algorithm.OUTPUT_NODES].features] == [1, 1]
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def test_classify_writes_graph_type_and_subnetwork(monkeypatch):
    algorithm = ClassifyAlgorithm()
    links = FakeSource(
        [
            FakeFeature({"id": "T1", "start": "A", "end": "B"}),
            FakeFeature({"id": "T2", "start": "B", "end": "C"}),
            FakeFeature({"id": "M1", "start": "D", "end": "E"}),
            FakeFeature({"id": "M2", "start": "E", "end": "F"}),
            FakeFeature({"id": "M3", "start": "F", "end": "D"}),
        ]
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_LINES: links},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id"}
    classifications = [feature.attributes()[-2:] for feature in sinks[algorithm.OUTPUT_LINES].features]
    assert ["BRANCHED", 1] in classifications
    assert ["MESHED", 1] in classifications
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def test_connect_by_distance_writes_nearest_connections_and_crs_error(monkeypatch):
    algorithm = ConnectByDistanceAlgorithm()
    monkeypatch.setattr("wnt.processes.wnt_connect_by_distance.QgsFeature", FakeOutputFeature)
    source = FakeSource(
        [
            FakeFeature({"id": "S1"}, FakeGeometry(0, 0)),
            FakeFeature({"id": "S2"}, FakeGeometry(10, 0)),
        ]
    )
    target = FakeSource(
        [
            FakeFeature({"id": "T1"}, FakeGeometry(1, 0)),
            FakeFeature({"id": "T2"}, FakeGeometry(3, 0)),
            FakeFeature({"id": "T3"}, FakeGeometry(20, 0)),
        ]
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_SOURCE: source, algorithm.INPUT_TARGET: target},
        fields={algorithm.MAX_CONNECTIONS: 1, algorithm.MAX_DISTANCE: 5},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT_CONNECTIONS: f"{algorithm.OUTPUT_CONNECTIONS}_id"}
    attrs = [feature.attributes_value for feature in sinks[algorithm.OUTPUT_CONNECTIONS].features]
    assert attrs == [["S1", "T1", 1.0, 1]]
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}

    bad_target = FakeSource([], crs=FakeCrs("EPSG:4326"))
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_SOURCE: source, algorithm.INPUT_TARGET: bad_target},
        fields={algorithm.MAX_CONNECTIONS: 1, algorithm.MAX_DISTANCE: 5},
    )
    feedback = FakeFeedback()

    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Layers have different CRS"]


def test_elevation_from_raster_processes_and_skips_nodes(monkeypatch):
    algorithm = ElevationFromRasterAlgorithm()
    nodes = FakeSource(
        [
            FakeFeature({"id": "N1", "elevation": 0}, FakeGeometry(1, 2)),
            FakeFeature({"id": "N2", "elevation": 0}, FakeGeometry(-1, 2)),
        ]
    )
    raster = FakeRaster()
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_DEM: raster},
        fields={algorithm.FIELD_ELEVATION: "elevation"},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT: f"{algorithm.OUTPUT}_id"}
    assert sinks[algorithm.OUTPUT].features[0]["elevation"] == 3
    assert len(sinks[algorithm.OUTPUT].features) == 1
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}

    bad_raster = FakeRaster(FakeCrs("EPSG:4326"))
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_DEM: bad_raster},
        fields={algorithm.FIELD_ELEVATION: "elevation"},
    )
    feedback = FakeFeedback()

    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Layers have different CRS"]


def test_elevation_from_tin_interpolates_nodes(monkeypatch, tmp_path):
    algorithm = ElevationFromTINAlgorithm()
    nodes = FakeSource(
        [
            FakeFeature({"id": "N1", "elevation": 0}, FakeGeometry(0.25, 0.25)),
            FakeFeature({"id": "N2", "elevation": 0}, FakeGeometry(5, 5)),
        ]
    )
    xml = tmp_path / "surface.xml"
    xml.write_text(
        """
        <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
          <Surfaces>
            <Surface name="Ground">
              <Metadata />
              <Definition surfType="TIN">
                <Pnts>
                  <P id="1">0 0 1</P>
                  <P id="2">0 1 2</P>
                  <P id="3">1 0 3</P>
                </Pnts>
                <Faces><F>1 2 3</F></Faces>
              </Definition>
            </Surface>
          </Surfaces>
        </LandXML>
        """,
        encoding="utf-8",
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes},
        fields={algorithm.FIELD_ELEVATION: "elevation", algorithm.SURFACE_NAME: "Ground"},
        files={algorithm.INPUT_TIN: xml},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT: f"{algorithm.OUTPUT}_id"}
    assert sinks[algorithm.OUTPUT].features[0]["elevation"] == pytest.approx(1.75)
    assert sinks[algorithm.OUTPUT].features[1]["elevation"] is None
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def test_hydrant_pairs_writes_pairs_within_distance(monkeypatch):
    algorithm = HydrantPairsAlgorithm()
    monkeypatch.setattr("wnt.processes.wnt_hydrant_pairs.QgsFeature", FakeOutputFeature)
    monkeypatch.setattr("wnt.processes.wnt_hydrant_pairs.QgsPoint", lambda point: point)
    monkeypatch.setattr("wnt.processes.wnt_hydrant_pairs.QgsLineString", lambda points: points)
    hydrants = FakeSource(
        [
            FakeFeature({"hid": "H1"}, FakeGeometry(0, 0)),
            FakeFeature({"hid": "H2"}, FakeGeometry(3, 4)),
            FakeFeature({"hid": "H3"}, FakeGeometry(20, 0)),
        ]
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_HYDRANTS: hydrants},
        fields={algorithm.FIELD_ID: "hid", algorithm.MAX_DISTANCE: 5},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT_PAIRS: f"{algorithm.OUTPUT_PAIRS}_id"}
    assert [feature.attributes_value for feature in sinks[algorithm.OUTPUT_PAIRS].features] == [
        ["0", "H1", "H2", 5.0]
    ]
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def epanet_template_text():
    return (
        "[TITLE]\n[JUNCTIONS]\n[RESERVOIRS]\n[TANKS]\n[PIPES]\n[PUMPS]\n"
        "[VALVES]\n[COORDINATES]\n[VERTICES]\n[BACKDROP]\nDIMENSIONS 0 0 0 0\n[END]\n"
    )


def test_epanet_from_network_exports_file_and_rejects_crs(monkeypatch, tmp_path):
    algorithm = EpanetFromNetworkAlgorithm()
    INPUT_TEMPLATE = tmp_path / "template.inp"
    output = tmp_path / "model.inp"
    INPUT_TEMPLATE.write_text(epanet_template_text(), encoding="latin-1")
    nodes = FakeSource(
        [
            FakeFeature({"id": "J1", "type": "JUNCTION", "elevation": 1}, FakeGeometry(0, 0)),
            FakeFeature({"id": "J2", "type": "RESERVOIR", "elevation": 2}, FakeGeometry(1, 0)),
        ]
    )
    links = FakeSource(
        [
            FakeFeature(
                {"id": "P1", "start": "J1", "end": "J2", "type": "PIPE", "length": 1.0},
                FakeGeometry(0, 0, "LineString(0 0, 1 0)"),
            )
        ]
    )
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_LINES: links},
        files={algorithm.INPUT_TEMPLATE: INPUT_TEMPLATE, algorithm.OUTPUT: output},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT: str(output)}
    text = output.read_text(encoding="latin-1")
    assert "J1    1.0    0.0" in text
    assert "P1    J1    J2" in text
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}

    bad_links = FakeSource([], crs=FakeCrs("EPSG:4326"))
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_LINES: bad_links},
        files={algorithm.INPUT_TEMPLATE: INPUT_TEMPLATE, algorithm.OUTPUT: output},
    )
    feedback = FakeFeedback()

    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Layers have different CRS"]


def test_network_from_epanet_imports_node_and_link_features(monkeypatch, tmp_path):
    algorithm = NetworkFromEpanetAlgorithm()
    inp = tmp_path / "example.inp"
    inp.write_text(
        """
        [JUNCTIONS]
        J1 1 5 PAT_J
        J2 2
        [RESERVOIRS]
        R1 100 PAT_R
        [TANKS]
        T1 10 1 0 5 15 0 VC1
        [COORDINATES]
        J1 0 0
        J2 1 0
        R1 2 0
        T1 3 0
        [PIPES]
        P1 J1 J2 1.0 100 120 0 Open
        [PUMPS]
        PU1 J2 R1 POWER 10 SPEED 1.2 PATTERN PAT_P
        [VALVES]
        V1 R1 T1 50 PRV 20 0.1
        [END]
        """,
        encoding="latin-1",
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        fields={algorithm.CRS: FakeCrs()},
        files={algorithm.INPUT: inp},
    )

    context = FakeProcessingContext()
    result = algorithm.processAlgorithm({}, context, FakeFeedback())

    assert result == {
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
        algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id",
    }
    assert context.layer_details[f"{algorithm.OUTPUT_NODES}_id"].name == "example_nodes"
    assert context.layer_details[f"{algorithm.OUTPUT_LINES}_id"].name == "example_links"
    nodes = {
        feature.attributes()[0]: feature.attributes()
        for feature in sinks[algorithm.OUTPUT_NODES].features
    }
    links = {
        feature.attributes()[0]: feature.attributes()
        for feature in sinks[algorithm.OUTPUT_LINES].features
    }
    assert nodes["J1"] == [
        "J1",
        "JUNCTION",
        1.0,
        "5",
        "PAT_J",
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]
    assert nodes["R1"] == [
        "R1",
        "RESERVOIR",
        100.0,
        None,
        "PAT_R",
        "100",
        None,
        None,
        None,
        None,
        None,
        None,
    ]
    assert nodes["T1"] == [
        "T1",
        "TANK",
        10.0,
        None,
        None,
        None,
        "1",
        "0",
        "5",
        "15",
        "0",
        "VC1",
    ]
    assert links["P1"] == [
        "P1",
        "J1",
        "J2",
        "PIPE",
        "1.0",
        "100",
        "120",
        "0",
        "Open",
        None,
        None,
        None,
        None,
        None,
        None,
    ]
    assert links["PU1"] == [
        "PU1",
        "J2",
        "R1",
        "PUMP",
        None,
        None,
        None,
        None,
        None,
        None,
        "10",
        None,
        "1.2",
        "PAT_P",
        "POWER 10 SPEED 1.2 PATTERN PAT_P",
    ]
    assert links["V1"] == [
        "V1",
        "R1",
        "T1",
        "PRV",
        None,
        "50",
        None,
        "0.1",
        None,
        "20",
        None,
        None,
        None,
        None,
        None,
    ]
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def test_network_from_landxml_imports_features(monkeypatch, tmp_path):
    algorithm = NetworkFromLandXMLAlgorithm()
    xml = tmp_path / "network.xml"
    xml.write_text(
        """
        <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
          <CoordinateSystem epsgCode="25830" />
          <PipeNetwork name="Storm" pipeNetType="storm">
            <Struct name="S1" desc="Inlet" elevSump="1" elevRim="3">
              <Center>10 20</Center>
              <Invert refPipe="P1" elev="1.5" />
            </Struct>
            <Struct name="S2" desc="Outlet" elevSump="2" elevRim="5">
              <Center>11 21</Center>
              <Invert refPipe="P1" elev="2.5" />
            </Struct>
            <Pipe name="P1" refStart="S1" refEnd="S2" length="12" slope="0.01">
              <CircPipe diameter="300" />
            </Pipe>
          </PipeNetwork>
        </LandXML>
        """,
        encoding="utf-8",
    )
    sinks = bind_common_parameters(monkeypatch, algorithm, files={algorithm.INPUT: xml})

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
        algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id",
    }
    assert len(sinks[algorithm.OUTPUT_NODES].features) == 2
    assert sinks[algorithm.OUTPUT_LINES].features[0].attributes()[2:5] == ["P1", "S1", "S2"]
    assert sinks[algorithm.OUTPUT_NODES].features[0].geometry().asWkt().startswith("Point")
    assert sinks[algorithm.OUTPUT_LINES].features[0].geometry().asWkt().startswith("LineString")
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def patch_lightweight_qgis_feature_classes(monkeypatch, module_name):
    monkeypatch.setattr(f"{module_name}.QgsFeature", FakeOutputFeature)
    monkeypatch.setattr(f"{module_name}.QgsField", lambda name, *args, **kwargs: FakeNamedField(name))
    monkeypatch.setattr(
        f"{module_name}.QgsFields",
        lambda fields=None: FakeFields(list(fields or [])),
    )
    monkeypatch.setattr(
        f"{module_name}.QgsPoint",
        lambda point, *args: point if not args else FakePoint(point, args[0]),
        raising=False,
    )
    monkeypatch.setattr(f"{module_name}.QgsLineString", lambda points: points, raising=False)


def test_assign_demand_accumulates_nearest_target(monkeypatch):
    algorithm = AssignDemandAlgorithm()
    patch_lightweight_qgis_feature_classes(monkeypatch, "wnt.processes.wnt_assign_demand")
    monkeypatch.setattr("wnt.processes.wnt_assign_demand.QgsSpatialIndex", FakeSpatialIndex)
    FIELDS_SOURCE = FakeFields([FakeNamedField("id"), FakeNamedField("base"), FakeNamedField("fire")])
    target_fields = FakeFields([FakeNamedField("id")])
    sources = FakeSource(
        [
            FakeFeature({"id": "S1", "base": 1.0, "fire": 2.0}, FakeGeometry(0, 0), fid=1),
            FakeFeature({"id": "S2", "base": 3.0, "fire": 4.0}, FakeGeometry(10, 0), fid=2),
        ],
        fields=FIELDS_SOURCE,
    )
    targets = FakeSource(
        [
            FakeFeature({"id": "T1"}, FakeGeometry(1, 0), fid=101),
            FakeFeature({"id": "T2"}, FakeGeometry(9, 0), fid=102),
        ],
        fields=target_fields,
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_SOURCE: sources, algorithm.INPUT_TARGET: targets},
        fields={algorithm.FIELDS_SOURCE: ["base", "fire"]},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {
        algorithm.OUTPUT_ASSIGNMENTS: f"{algorithm.OUTPUT_ASSIGNMENTS}_id",
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
    }
    assignment_attrs = [
        feature.attributes_value for feature in sinks[algorithm.OUTPUT_ASSIGNMENTS].features
    ]
    node_attrs = [feature.attributes_value for feature in sinks[algorithm.OUTPUT_NODES].features]
    assert assignment_attrs == [["S1", "T1", 1.0, 2.0], ["S2", "T2", 3.0, 4.0]]
    assert node_attrs == [["T1", 1.0, 2.0], ["T2", 3.0, 4.0]]
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}

    bad_targets = FakeSource([], crs=FakeCrs("EPSG:4326"))
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_SOURCE: sources, algorithm.INPUT_TARGET: bad_targets},
        fields={algorithm.FIELDS_SOURCE: ["base"]},
    )
    feedback = FakeFeedback()
    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Layers have different CRS"]


def test_update_assignment_updates_moved_target_and_errors(monkeypatch):
    algorithm = UpdateAssignmentAlgorithm()
    fields = FakeFields([FakeNamedField("source"), FakeNamedField("target"), FakeNamedField("base")])
    sources = FakeSource(
        [FakeFeature({"id": "S1", "base": 5.0}, FakeGeometry(0, 0))],
        fields=FakeFields([FakeNamedField("id"), FakeNamedField("base")]),
    )
    targets = FakeSource(
        [
            FakeFeature({"id": "T1", "base": 0.0}, FakeGeometry(1, 0)),
            FakeFeature({"id": "T2", "base": 0.0}, FakeGeometry(2, 0)),
        ],
        fields=FakeFields([FakeNamedField("id"), FakeNamedField("base")]),
    )
    assignments = FakeSource(
        [
            FakeFeature(
                {"source": "S1", "target": "T1", "base": 0.0},
                FakeGeometry(0, 0, polyline=[FakePoint(0, 0), FakePoint(2, 0)]),
            )
        ],
        fields=fields,
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={
            algorithm.INPUT_SOURCE: sources,
            algorithm.INPUT_TARGET: targets,
            algorithm.INPUT_ASSIGNMENTS: assignments,
        },
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {
        algorithm.OUTPUT_ASSIGNMENTS: f"{algorithm.OUTPUT_ASSIGNMENTS}_id",
        algorithm.OUTPUT_TARGETS: f"{algorithm.OUTPUT_TARGETS}_id",
    }
    assert sinks[algorithm.OUTPUT_ASSIGNMENTS].features[0]["target"] == "T2"
    assert [feature["base"] for feature in sinks[algorithm.OUTPUT_TARGETS].features] == [0, 5.0]
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}

    misplaced = FakeSource(
        [
            FakeFeature(
                {"source": "S1", "target": "T1", "base": 0.0},
                FakeGeometry(0, 0, polyline=[FakePoint(9, 9), FakePoint(1, 0)]),
            )
        ],
        fields=fields,
    )
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={
            algorithm.INPUT_SOURCE: sources,
            algorithm.INPUT_TARGET: targets,
            algorithm.INPUT_ASSIGNMENTS: misplaced,
        },
    )
    feedback = FakeFeedback()
    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Source point misplaced: S1"]


def test_split_lines_at_points_splits_and_keeps_original(monkeypatch):
    algorithm = SplitLinesAtPointsAlgorithm()

    points = FakeSource(
        [
            FakeFeature({"id": "P1"}, QgsGeometry.fromPointXY(QgsPointXY(1, 0))),
            FakeFeature({"id": "P2"}, QgsGeometry.fromPointXY(QgsPointXY(1.0001, 0))),
            FakeFeature({"id": "P3"}, QgsGeometry.fromPointXY(QgsPointXY(10, 10))),
        ]
    )
    lines = FakeSource(
        [
            FakeFeature({"id": "L1"}, QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(2, 0)])),
            FakeFeature({"id": "L2"}, QgsGeometry.fromPolylineXY([QgsPointXY(0, 1), QgsPointXY(2, 1)])),
        ]
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_POINTS: points, algorithm.INPUT_LINES: lines},
        fields={algorithm.TOLERANCE: 0.01},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT: f"{algorithm.OUTPUT}_id"}
    assert len(sinks[algorithm.OUTPUT].features) == 3
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}

    bad_lines = FakeSource([], crs=FakeCrs("EPSG:4326"))
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_POINTS: points, algorithm.INPUT_LINES: bad_lines},
        fields={algorithm.TOLERANCE: 0.01},
    )
    feedback = FakeFeedback()
    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Layers have different CRS"]


def test_merge_networks_aligns_fields_and_warns_for_offset_connections(monkeypatch):
    algorithm = MergeNetworksAlgorithm()
    monkeypatch.setattr("wnt.processes.wnt_merge_networks.QgsFeature", FakeOutputFeature)
    node_fields_1 = FakeFields([FakeNamedField("id"), FakeNamedField("elevation")])
    node_fields_2 = FakeFields([FakeNamedField("id"), FakeNamedField("zone")])
    link_fields_1 = FakeFields([FakeNamedField("id"), FakeNamedField("start"), FakeNamedField("end")])
    link_fields_2 = FakeFields([FakeNamedField("id"), FakeNamedField("diameter")])
    n1 = FakeSource(
        [
            FakeFeature({"id": "N1", "elevation": 1}, FakeGeometry(0, 0)),
            FakeFeature({"id": "N2", "elevation": 2}, FakeGeometry(1, 0)),
        ],
        fields=node_fields_1,
    )
    n2 = FakeSource(
        [
            FakeFeature({"id": "N2", "zone": "B"}, FakeGeometry(2, 0)),
            FakeFeature({"id": "N3", "zone": "C"}, FakeGeometry(3, 0)),
        ],
        fields=node_fields_2,
    )
    l1 = FakeSource(
        [FakeFeature({"id": "L1", "start": "N1", "end": "N2"}, FakeGeometry(0, 0))],
        fields=link_fields_1,
    )
    l2 = FakeSource(
        [FakeFeature({"id": "L2", "diameter": 100}, FakeGeometry(0, 0))],
        fields=link_fields_2,
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={
            algorithm.INPUT_NODES_1: n1,
            algorithm.INPUT_LINES_1: l1,
            algorithm.INPUT_NODES_2: n2,
            algorithm.INPUT_LINES_2: l2,
        },
    )
    feedback = FakeFeedback()

    result = algorithm.processAlgorithm({}, None, feedback)

    assert result == {
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
        algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id",
    }
    assert [feature.attributes_value for feature in sinks[algorithm.OUTPUT_NODES].features] == [
        ["N1", 1, None],
        ["N2", 2, None],
        ["N3", None, "C"],
    ]
    assert [feature.attributes_value for feature in sinks[algorithm.OUTPUT_LINES].features] == [
        ["L1", "N1", "N2", None],
        ["L2", None, None, 100],
    ]
    assert any("Connection node N2 distance is 1.0" in line for line in feedback.info)
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}

    bad = FakeSource([], crs=FakeCrs("EPSG:4326"))
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={
            algorithm.INPUT_NODES_1: n1,
            algorithm.INPUT_LINES_1: l1,
            algorithm.INPUT_NODES_2: bad,
            algorithm.INPUT_LINES_2: l2,
        },
    )
    feedback = FakeFeedback()
    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Layers have different CRS"]


def test_aligned_feature_fills_missing_fields(monkeypatch):
    monkeypatch.setattr("wnt.processes.wnt_merge_networks.QgsFeature", FakeOutputFeature)
    feature = FakeFeature({"id": "N1"}, FakeGeometry(0, 0))
    result = aligned_feature(feature, FakeFields([FakeNamedField("id"), FakeNamedField("missing")]))

    assert result.attributes_value == ["N1", None]


def test_network_from_lines_builds_node_and_link_outputs(monkeypatch):
    algorithm = NetworkFromLinesAlgorithm()
    patch_lightweight_qgis_feature_classes(monkeypatch, "wnt.processes.wnt_network_from_lines")
    monkeypatch.setattr("wnt.processes.wnt_network_from_lines.QgsPointXY", lambda x, y: FakePoint(x, y))
    monkeypatch.setattr("wnt.processes.wnt_network_from_lines.QgsGeometry", FakeQgsGeometry)
    fields = FakeFields([FakeNamedField("material")])
    lines = FakeSource(
        [
            FakeFeature(
                {"material": "PVC"},
                FakeGeometry(0, 0, polyline=[FakePoint(0, 0), FakePoint(1, 0)]),
                fid=11,
            ),
            FakeFeature(
                {"material": "DI"},
                FakeGeometry(1, 0, polyline=[FakePoint(1, 0), FakePoint(2, 0)]),
                fid=12,
            ),
        ],
        fields=fields,
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT: lines},
        fields={
            algorithm.TOLERANCE: 0.001,
            algorithm.MASK_NODE: "N$",
            algorithm.INITIAL_NODE: 1,
            algorithm.INCREMENT_NODE: 1,
            algorithm.MASK_LINK: "L$",
            algorithm.INITIAL_LINK: 1,
            algorithm.INCREMENT_LINK: 1,
        },
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
        algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id",
    }
    assert [feature.attributes_value for feature in sinks[algorithm.OUTPUT_NODES].features] == [
        ["N1", "", 0.0],
        ["N2", "", 0.0],
        ["N3", "", 0.0],
    ]
    assert [feature.attributes_value[:5] for feature in sinks[algorithm.OUTPUT_LINES].features] == [
        ["L1", "N1", "N2", "PIPE", 1.0],
        ["L2", "N2", "N3", "PIPE", 1.0],
    ]
    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def test_network_from_lines_splits_multipart_and_uses_z_elevations(monkeypatch):
    algorithm = NetworkFromLinesAlgorithm()
    patch_lightweight_qgis_feature_classes(monkeypatch, "wnt.processes.wnt_network_from_lines")
    monkeypatch.setattr("wnt.processes.wnt_network_from_lines.QgsPointXY", lambda x, y: FakePoint(x, y))
    monkeypatch.setattr("wnt.processes.wnt_network_from_lines.QgsGeometry", FakeQgsGeometry)
    fields = FakeFields([FakeNamedField("material")])
    lines = FakeSource(
        [
            FakeFeature(
                {"material": "PVC"},
                FakeGeometry(
                    0,
                    0,
                    multipolyline=[
                        [FakePoint(0, 0, 10.0), FakePoint(1, 0, 11.0)],
                        [FakePoint(1, 0, 11.0004), FakePoint(2, 0, 12.0)],
                    ],
                ),
                fid=11,
            ),
        ],
        fields=fields,
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT: lines},
        fields={
            algorithm.TOLERANCE: 0.001,
            algorithm.MASK_NODE: "N$",
            algorithm.INITIAL_NODE: 1,
            algorithm.INCREMENT_NODE: 1,
            algorithm.MASK_LINK: "L$",
            algorithm.INITIAL_LINK: 1,
            algorithm.INCREMENT_LINK: 1,
            algorithm.USE_LINE_ELEVATION: True,
        },
    )

    context = FakeProcessingContext()
    result = algorithm.processAlgorithm({}, context, FakeFeedback())

    assert result == {
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
        algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id",
    }
    assert [feature.attributes_value for feature in sinks[algorithm.OUTPUT_NODES].features] == [
        ["N1", "", 10.0],
        ["N2", "", pytest.approx(11.0002)],
        ["N3", "", 12.0],
    ]
    assert [feature.attributes_value for feature in sinks[algorithm.OUTPUT_LINES].features] == [
        ["L1", "N1", "N2", "PIPE", 1.0, "PVC"],
        ["L2", "N2", "N3", "PIPE", 1.0, "PVC"],
    ]


def test_network_from_lines_extracts_qgis_multiline_parts_with_z():
    multiline = QgsMultiLineString()
    multiline.addGeometry(QgsLineString([QgsPoint(0, 0, 10), QgsPoint(1, 0, 11)]))
    multiline.addGeometry(QgsLineString([QgsPoint(1, 0, 11), QgsPoint(2, 0, 12)]))

    parts = NetworkFromLinesAlgorithm._line_parts(QgsGeometry(multiline))

    assert len(parts) == 2
    assert parts[0][0].z() == 10
    assert parts[1][-1].z() == 12


def test_network_from_lines_rejects_conflicting_z_elevations(monkeypatch):
    algorithm = NetworkFromLinesAlgorithm()
    patch_lightweight_qgis_feature_classes(monkeypatch, "wnt.processes.wnt_network_from_lines")
    lines = FakeSource(
        [
            FakeFeature(
                {},
                FakeGeometry(0, 0, polyline=[FakePoint(0, 0, 10.0), FakePoint(1, 0, 11.0)]),
            ),
            FakeFeature(
                {},
                FakeGeometry(1, 0, polyline=[FakePoint(1, 0, 11.5), FakePoint(2, 0, 12.0)]),
            ),
        ]
    )
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT: lines},
        fields={
            algorithm.TOLERANCE: 0.001,
            algorithm.MASK_NODE: "N$",
            algorithm.INITIAL_NODE: 1,
            algorithm.INCREMENT_NODE: 1,
            algorithm.MASK_LINK: "L$",
            algorithm.INITIAL_LINK: 1,
            algorithm.INCREMENT_LINK: 1,
            algorithm.USE_LINE_ELEVATION: True,
        },
    )

    feedback = FakeFeedback()
    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == [
        "ERROR: Line endpoint elevations merged into a node differ more than tolerance"
    ]


def test_network_from_lines_rejects_invalid_and_looped(monkeypatch):
    algorithm = NetworkFromLinesAlgorithm()
    invalid = FakeSource([FakeFeature({}, FakeGeometry(0, 0, polyline=[FakePoint(0, 0)]), fid=7)])
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT: invalid},
        fields={
            algorithm.TOLERANCE: 0.001,
            algorithm.MASK_NODE: "N$",
            algorithm.INITIAL_NODE: 1,
            algorithm.INCREMENT_NODE: 1,
            algorithm.MASK_LINK: "L$",
            algorithm.INITIAL_LINK: 1,
            algorithm.INCREMENT_LINK: 1,
        },
    )
    feedback = FakeFeedback()
    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Invalid LineString geometry (FID: 7)"]

    looped = FakeSource(
        [
            FakeFeature(
                {},
                FakeGeometry(0, 0, polyline=[FakePoint(0, 0), FakePoint(0.0001, 0)]),
                fid=8,
            )
        ]
    )
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT: looped},
        fields={
            algorithm.TOLERANCE: 0.001,
            algorithm.MASK_NODE: "N$",
            algorithm.INITIAL_NODE: 1,
            algorithm.INCREMENT_NODE: 1,
            algorithm.MASK_LINK: "L$",
            algorithm.INITIAL_LINK: 1,
            algorithm.INCREMENT_LINK: 1,
        },
    )
    feedback = FakeFeedback()
    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Looped LineString detected (FID: 8)"]


class FakeEpanetLibrary:
    def __init__(self, error_at=None, link_status=1.0):
        self.error_at = error_at
        self.link_status = link_status
        self.calls = {}
        self.next_calls = 0

    def _err(self, name):
        self.calls[name] = self.calls.get(name, 0) + 1
        if self.error_at == name:
            return 77
        if self.error_at == (name, self.calls[name]):
            return 77
        return 0

    def ENgetversion(self, out):
        err = self._err("ENgetversion")
        if err:
            return err
        out._obj.value = 20200
        return 0

    def ENgeterror(self, code, out, max_len):
        value = f"EPANET toolkit error {code}".encode()
        if hasattr(out, "_obj"):
            out._obj.value = value
        else:
            out.value = value
        return 0

    def ENopen(self, inp, rpt, out=None):
        return self._err("ENopen")

    def ENgetcount(self, code, out):
        err = self._err("ENgetcount")
        if err:
            return err
        out._obj.value = 1
        return 0

    def ENopenH(self):
        return self._err("ENopenH")

    def ENinitH(self, save):
        return self._err("ENinitH")

    def ENrunH(self, out):
        err = self._err("ENrunH")
        if err:
            return err
        out._obj.value = self.next_calls * 3600
        return 0

    def ENgetnodeid(self, index, out):
        err = self._err("ENgetnodeid")
        if err:
            return err
        if hasattr(out, "_obj"):
            out._obj.value = b"N1"
        else:
            out.value = b"N1"
        return 0

    def ENgetnodevalue(self, index, parameter, out):
        err = self._err("ENgetnodevalue")
        if err:
            return err
        out._obj.value = float(parameter)
        return 0

    def ENgetlinkid(self, index, out):
        err = self._err("ENgetlinkid")
        if err:
            return err
        if hasattr(out, "_obj"):
            out._obj.value = b"L1"
        else:
            out.value = b"L1"
        return 0

    def ENgetlinkvalue(self, index, parameter, out):
        err = self._err("ENgetlinkvalue")
        if err:
            return err
        out._obj.value = self.link_status if parameter == 11 else float(parameter)
        return 0

    def ENnextH(self, out):
        err = self._err("ENnextH")
        if err:
            return err
        self.next_calls += 1
        out._obj.value = 0
        return 0

    def ENclose(self):
        return self._err("ENclose")


class FakeToolkitConfig:
    def __init__(self, has_lib=True):
        self.has_lib = has_lib

    def read(self, path):
        return []

    def __getitem__(self, key):
        if not self.has_lib:
            raise KeyError(key)
        return {"lib": "fake-epanet"}


def patch_results_algorithm(monkeypatch, library=None, has_lib=True):
    patch_lightweight_qgis_feature_classes(monkeypatch, "wnt.processes.wnt_results_from_epanet")
    if has_lib:
        monkeypatch.setattr(
            "wnt.processes.wnt_results_from_epanet.EpanetToolkit.from_config",
            lambda: EpanetToolkit(library or FakeEpanetLibrary(), "fake-epanet"),
        )
    else:
        monkeypatch.setattr(
            "wnt.processes.wnt_results_from_epanet.EpanetToolkit.from_config",
            lambda: (_ for _ in ()).throw(
                EpanetConfigurationError("Configure EPANET toolkit library")
            ),
        )


def test_results_from_epanet_loads_node_and_link_results(monkeypatch, tmp_path):
    algorithm = ResultsFromEpanetAlgorithm()
    inp = tmp_path / "model.inp"
    inp.write_text("[END]\n", encoding="utf-8")
    patch_results_algorithm(monkeypatch)
    sinks = bind_common_parameters(monkeypatch, algorithm, files={algorithm.INPUT: inp})

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
        algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id",
    }
    node_attrs = sinks[algorithm.OUTPUT_NODES].features[0].attributes_value
    link_attrs = sinks[algorithm.OUTPUT_LINES].features[0].attributes_value
    node_attrs[1] = node_attrs[1].rstrip("\x00")
    link_attrs[1] = link_attrs[1].rstrip("\x00")
    assert node_attrs == [
        "00:00:00",
        "N1",
        9.0,
        10.0,
        11.0,
    ]
    assert link_attrs == [
        "00:00:00",
        "L1",
        8.0,
        9.0,
        10.0,
        "OPEN",
        12.0,
        13.0,
    ]


def test_epanet_constants_are_resolved_by_toolkit_version():
    assert constants_for_version(20012).max_label_len == 15
    assert constants_for_version(20200).max_label_len == 31
    assert constants_for_version(20200).node_count == 0
    assert constants_for_version(20200).energy == 13


def test_results_from_epanet_loads_posix_library_and_closed_status(monkeypatch, tmp_path):
    algorithm = ResultsFromEpanetAlgorithm()
    inp = tmp_path / "model.inp"
    inp.write_text("[END]\n", encoding="utf-8")

    patch_results_algorithm(monkeypatch, FakeEpanetLibrary(link_status=0.0))
    sinks = bind_common_parameters(monkeypatch, algorithm, files={algorithm.INPUT: inp})

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
        algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id",
    }
    assert sinks[algorithm.OUTPUT_LINES].features[0].attributes_value[5] == "CLOSED"


def test_results_from_epanet_reports_configuration_and_toolkit_errors(monkeypatch, tmp_path):
    algorithm = ResultsFromEpanetAlgorithm()
    inp = tmp_path / "model.inp"
    inp.write_text("[END]\n", encoding="utf-8")
    patch_results_algorithm(monkeypatch, has_lib=False)
    bind_common_parameters(monkeypatch, algorithm, files={algorithm.INPUT: inp})
    feedback = FakeFeedback()

    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Configure EPANET toolkit library"]

    patch_results_algorithm(monkeypatch, FakeEpanetLibrary(error_at="ENopen"))
    bind_common_parameters(monkeypatch, algorithm, files={algorithm.INPUT: inp})
    feedback = FakeFeedback()

    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: EPANET toolkit error 77"]


@pytest.mark.parametrize(
    "error_at",
    [
        "ENgetcount",
        ("ENgetcount", 2),
        "ENopenH",
        "ENinitH",
        "ENgetnodeid",
        "ENgetnodevalue",
        "ENgetlinkid",
        ("ENgetlinkvalue", 1),
        ("ENgetlinkvalue", 4),
        ("ENgetlinkvalue", 5),
        "ENnextH",
        "ENclose",
    ],
)
def test_results_from_epanet_reports_toolkit_errors_at_each_step(monkeypatch, tmp_path, error_at):
    algorithm = ResultsFromEpanetAlgorithm()
    inp = tmp_path / "model.inp"
    inp.write_text("[END]\n", encoding="utf-8")
    patch_results_algorithm(monkeypatch, FakeEpanetLibrary(error_at=error_at))
    bind_common_parameters(monkeypatch, algorithm, files={algorithm.INPUT: inp})
    feedback = FakeFeedback()

    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: EPANET toolkit error 77"]


def test_results_from_epanet_returns_empty_when_canceled(monkeypatch, tmp_path):
    algorithm = ResultsFromEpanetAlgorithm()
    inp = tmp_path / "model.inp"
    inp.write_text("[END]\n", encoding="utf-8")
    patch_results_algorithm(monkeypatch)
    bind_common_parameters(monkeypatch, algorithm, files={algorithm.INPUT: inp})

    assert algorithm.processAlgorithm({}, None, FakeFeedback(canceled=True)) == {}


def test_config_toolkit_writes_ini(monkeypatch, tmp_path):
    algorithm = ConfigToolkitAlgorithm()
    ini = tmp_path / "toolkit.ini"

    class FakeConfiguredToolkit:
        def check_available(self):
            return True

        def info(self):
            return ToolkitInfo(
                library_path=str(tmp_path / "epanet.dll"),
                platform="Windows",
                architecture="AMD64",
                version="2.2.0",
                api="legacy",
            )

    monkeypatch.setattr("wnt.processes.wnt_config_toolkit.toolkit_config_path", lambda: ini)
    monkeypatch.setattr(
        "wnt.processes.wnt_config_toolkit.EpanetToolkit.from_library_path",
        lambda lib_file: FakeConfiguredToolkit(),
    )
    bind_common_parameters(monkeypatch, algorithm, files={algorithm.INPUT: tmp_path / "epanet.dll"})

    feedback = FakeFeedback()
    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert "epanet.dll" in ini.read_text(encoding="utf-8")
    assert "Platform: Windows AMD64" in feedback.info
    assert "EPANET toolkit version: 2.2.0" in feedback.info


def test_validate_reports_all_problem_types(monkeypatch):
    algorithm = ValidateAlgorithm()
    nodes = FakeSource(
        [
            FakeFeature({"id": "N1"}),
            FakeFeature({"id": "N1"}),
            FakeFeature({"id": "ORPHAN"}),
        ]
    )
    links = FakeSource(
        [
            FakeFeature({"id": "L1", "start": "N1", "end": "MISSING"}),
            FakeFeature({"id": "L1", "start": "N1", "end": "N1"}),
        ]
    )
    sinks = bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_LINES: links},
    )

    feedback = FakeFeedback()
    result = algorithm.processAlgorithm({}, None, feedback)

    assert result == {
        algorithm.OUTPUT_NODES: f"{algorithm.OUTPUT_NODES}_id",
        algorithm.OUTPUT_LINES: f"{algorithm.OUTPUT_LINES}_id",
    }
    node_messages = [feature.attributes()[-1] for feature in sinks[algorithm.OUTPUT_NODES].features]
    link_messages = [feature.attributes()[-1] for feature in sinks[algorithm.OUTPUT_LINES].features]
    assert "Duplicated." in node_messages[0]
    assert "Orphan." in node_messages[2]
    assert "Undefined node links." in link_messages[0]
    assert "Duplicate link. Loop." in link_messages[1]
    assert any("problems detected" in line for line in feedback.info)


def test_ppno_from_network_writes_ext_and_rejects_crs(monkeypatch, tmp_path):
    algorithm = PpnoFromNetworkAlgorithm()
    INPUT_TEMPLATE = tmp_path / "template.ext"
    output = tmp_path / "output.ext"
    INPUT_EPANET = tmp_path / "model.inp"
    INPUT_TEMPLATE.write_text(
        textwrap.dedent(
            """
            [TITLE]
            [INP]
            [PRESSURES]
            [PIPES]
            [END]
            """
        ).strip(),
        encoding="latin-1",
    )
    nodes = FakeSource([FakeFeature({"id": "N1", "pressure": 20}), FakeFeature({"id": "N2", "pressure": 0})])
    links = FakeSource([FakeFeature({"id": "L1", "series": "S1"}), FakeFeature({"id": "L2", "series": ""})])
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_LINES: links},
        fields={algorithm.FIELD_PRESSURE: "pressure", algorithm.FIELD_SERIES: "series"},
        files={algorithm.INPUT_EPANET: INPUT_EPANET, algorithm.INPUT_TEMPLATE: INPUT_TEMPLATE, algorithm.OUTPUT: output},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT: str(output)}
    text = output.read_text(encoding="latin-1")
    assert "N1    20" in text
    assert "L1    S1" in text

    bad_links = FakeSource([], crs=FakeCrs("EPSG:4326"))
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes, algorithm.INPUT_LINES: bad_links},
        fields={algorithm.FIELD_PRESSURE: "pressure", algorithm.FIELD_SERIES: "series"},
        files={algorithm.INPUT_EPANET: INPUT_EPANET, algorithm.INPUT_TEMPLATE: INPUT_TEMPLATE, algorithm.OUTPUT: output},
    )
    feedback = FakeFeedback()

    assert algorithm.processAlgorithm({}, None, feedback) == {}
    assert feedback.errors == ["ERROR: Layers have different CRS"]


def test_scn_from_demands_writes_selected_junction_demands(monkeypatch, tmp_path):
    algorithm = ScnFromDemandsAlgorithm()
    output = tmp_path / "demands.scn"
    nodes = FakeSource(
        [
            FakeFeature({"id": "J1", "type": "JUNCTION", "base": 1.2, "fire": 0}),
            FakeFeature({"id": "R1", "type": "RESERVOIR", "base": 9.9, "fire": 1}),
            FakeFeature({"id": "J2", "type": "JUNCTION", "base": 2.5, "fire": 3.5}),
        ]
    )
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes},
        fields={algorithm.FIELD_DEMAND: ["base", "fire"]},
        files={algorithm.OUTPUT: output},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT: str(output)}
    text = output.read_text(encoding="utf-8")
    assert "J1  1.2  base" in text
    assert "J2  2.5  base" in text
    assert "J2  3.5  fire" in text
    assert "R1" not in text

    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_NODES: nodes},
        fields={algorithm.FIELD_DEMAND: []},
        files={algorithm.OUTPUT: output},
    )
    assert algorithm.processAlgorithm({}, None, FakeFeedback()) == {}


def test_scn_from_pipe_properties_writes_only_pipes(monkeypatch, tmp_path):
    algorithm = ScnFromPipePropertiesAlgorithm()
    output = tmp_path / "scenario.scn"
    links = FakeSource(
        [
            FakeFeature({"id": "P1", "type": "PIPE", "diameter": 100, "roughness": 120}),
            FakeFeature({"id": "V1", "type": "PRV", "diameter": 50, "roughness": 80}),
            FakeFeature({"id": "P2", "type": "CVPIPE", "diameter": 150, "roughness": 130}),
        ]
    )
    bind_common_parameters(
        monkeypatch,
        algorithm,
        sources={algorithm.INPUT_LINES: links},
        fields={algorithm.FIELD_DIAMETER: "diameter", algorithm.FIELD_ROUGHNESS: "roughness"},
        files={algorithm.OUTPUT: output},
    )

    result = algorithm.processAlgorithm({}, None, FakeFeedback())

    assert result == {algorithm.OUTPUT: str(output)}
    text = output.read_text(encoding="utf-8")
    assert "P1    100" in text
    assert "P2    150" in text
    assert "V1" not in text
