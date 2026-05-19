"""Additional coverage for pure utility modules."""

import textwrap

import pytest

from wnt.utils.core import (
    WntLink,
    WntNetwork,
    WntNode,
    format_id,
    net_from_linestrings,
    polyline_length,
    xy,
)
from wnt.utils.graph import Graph
from wnt.utils.landxml import network_from_xml
from wnt.utils.tin import TIN, Triangle


def test_xy_accepts_indexed_and_qgis_like_points():
    """Coordinate helpers work with tuples and objects exposing x/y methods."""

    class Point:
        def x(self):
            return 3

        def y(self):
            return 4

    assert xy((1, 2, 9)) == (1, 2)
    assert xy(Point()) == (3, 4)


def test_polyline_length_rejects_bad_geometry():
    with pytest.raises(ValueError, match="Bad geometry"):
        polyline_length([(0, 0), object()])


def test_format_id_masks_and_plain_prefixes():
    assert format_id(7, "N-$$") == "N-07"
    assert format_id(7, "NODE") == "NODE7"


def test_net_from_linestrings_error_and_union_branches():
    with pytest.raises(Exception, match="Zero length"):
        net_from_linestrings([[(0, 0), (0, 0)]], 0)
    with pytest.raises(Exception, match="Looped"):
        net_from_linestrings([[(0, 0), (0.001, 0)]], 0.01)

    nodes, links = net_from_linestrings(
        [
            [(0, 0), (1, 0)],
            [(1.01, 0), (2, 0)],
            [(2.01, 0), (3, 0)],
        ],
        0.02,
    )

    assert len(nodes) == 4
    assert links[0][1] == links[1][0]
    assert links[1][1] == links[2][0]


def test_node_validation_and_wkt_parsing():
    node = WntNode("J1")

    assert str(node) == "WntNode: J1."
    node.from_wkt('Point Z (1 2 3)')
    node.set_elevation("12.5")
    node.set_type("junction")

    assert node.get_geometry() == (1.0, 2.0)
    assert node.get_elevation() == 12.5
    assert node.get_type() == "JUNCTION"

    with pytest.raises(Exception, match="Bad geometry"):
        node.set_geometry(("x", 2))
    with pytest.raises(Exception, match="Bad elevation"):
        node.set_elevation("high")
    with pytest.raises(Exception, match="Incorrect type"):
        node.set_type("unknown")
    with pytest.raises(Exception, match="Incorrect type"):
        node.set_type(None)
    with pytest.raises(Exception, match="Incorrect WKT"):
        node.from_wkt("not a point")


def test_link_validation_wkt_and_accessors():
    link = WntLink("P1", "J1", "J2")

    assert str(link) == "WntLink: P1. J1 -> J2."
    assert link.name() == "P1"
    assert link.start() == "J1"
    assert link.end() == "J2"
    link.from_wkt('LineString Z (0 0 0, 1 0 0, 1 1 0)')
    link.set_type("pipe")

    assert link.get_startpoint() == (0.0, 0.0)
    assert link.get_endpoint() == (1.0, 1.0)
    assert link.get_vertices() == [(1.0, 0.0)]
    assert link.to_wkt() == "LineString(0.0 0.0,1.0 0.0,1.0 1.0)"
    assert link.length() == pytest.approx(2.0)
    assert link.get_type() == "PIPE"

    with pytest.raises(Exception, match="at least 2 points"):
        link.set_geometry([(0, 0)])
    with pytest.raises(Exception, match="Looped"):
        link.set_geometry([(0, 0), (0, 0)])
    with pytest.raises(Exception, match="Bad geometry"):
        link.set_geometry([(0, 0), ("bad", 1)])
    with pytest.raises(Exception, match="Bad type"):
        link.set_type("bad")
    with pytest.raises(Exception, match="Bad type"):
        link.set_type(None)
    with pytest.raises(Exception, match="Multi-geometry"):
        link.from_wkt("MultiLineString((0 0, 1 1))")
    with pytest.raises(Exception, match="Incorrect WKT"):
        link.from_wkt(None)
    with pytest.raises(Exception, match="Incorrect WKT"):
        link.from_wkt("LineString(bad)")


def test_network_validation_and_exports(tmp_path):
    network = WntNetwork()
    assert str(network) == "WntNetwork."
    j1 = WntNode("J1")
    j1.set_type("JUNCTION")
    j1.set_elevation(0)
    j1.set_geometry((0, 0))
    j2 = WntNode("J2")
    j2.set_type("RESERVOIR")
    j2.set_elevation(10)
    j2.set_geometry((1, 0))
    j3 = WntNode("J3")
    j3.set_type("TANK")
    j3.set_geometry((2, 0))
    duplicate = WntNode("J2")
    duplicate.set_geometry((3, 0))
    network.add_node(j1)
    network.add_node(j2)
    network.add_node(j3)
    network.add_node(duplicate)

    pipe = WntLink("P1", "J1", "J2")
    pipe.set_type("CVPIPE")
    pipe.epanet["length"] = 1.25
    pipe.set_geometry([(0, 0), (0.5, 0.2), (1, 0)])
    pump = WntLink("PU1", "J2", "J3")
    pump.set_type("PUMP")
    pump.set_geometry([(1, 0), (2, 0)])
    valve = WntLink("V1", "J3", "J3")
    valve.set_type("PRV")
    valve.set_geometry([(2, 0), (2, 1)])
    missing = WntLink("P1", "J3", "MISSING")
    missing.set_geometry([(2, 0), (3, 0)])
    network.add_link(pipe)
    network.add_link(pump)
    network.add_link(valve)
    network.add_link(missing)

    assert network.node(0) is j1
    assert network.link(0) is pipe
    with pytest.raises(Exception, match="Bad type"):
        network.add_node(object())
    with pytest.raises(Exception, match="Bad type"):
        network.add_link(object())

    assert network.validate() == {
        "orphan nodes": set(),
        "duplicate nodes": {"J2"},
        "undefined node links": {"P1"},
        "duplicate links": {"P1"},
        "loops": {"V1"},
    }

    tgf = tmp_path / "network.tgf"
    network.to_tgf(tgf)
    assert "0 J1" in tgf.read_text(encoding="utf-8")

    template = tmp_path / "template.inp"
    output = tmp_path / "output.inp"
    template.write_text(
        textwrap.dedent(
            """
            [TITLE]
            [JUNCTIONS]
            [RESERVOIRS]
            [TANKS]
            [PIPES]
            [PUMPS]
            [VALVES]
            [COORDINATES]
            [VERTICES]
            [BACKDROP]
            DIMENSIONS 0 0 0 0
            [END]
            """
        ).strip(),
        encoding="latin-1",
    )

    network.to_epanet(output, template)

    text = output.read_text(encoding="latin-1")
    assert "P1    J1    J2    1.25" in text
    assert "PU1    J2    J3" in text
    assert "V1    J3    J3" in text
    assert "DIMENSIONS" in text


def test_epanet_import_covers_all_supported_sections(tmp_path):
    inp = tmp_path / "full.inp"
    inp.write_text(
        textwrap.dedent(
            """
            [JUNCTIONS]
            J1 0
            J2 5
            [RESERVOIRS]
            R1 10
            [TANKS]
            T1 7
            [COORDINATES]
            J1 0 0
            J2 1 0
            R1 2 0
            T1 3 0
            UNKNOWN 9 9
            [PIPES]
            P1 J1 J2 1.0 100 120 0 CV
            P2 J2 R1 1.0 100 120 0 Open
            [PUMPS]
            PU1 R1 T1 HEAD 1
            [VALVES]
            V1 T1 J1 100 PRV 0 0
            [VERTICES]
            P1 0.5 0.5
            UNKNOWN 8 8
            [END]
            """
        ).strip(),
        encoding="latin-1",
    )

    network = WntNetwork()
    network.from_epanet(inp)

    assert [node.get_type() for node in network.nodes()] == [
        "JUNCTION",
        "JUNCTION",
        "RESERVOIR",
        "TANK",
    ]
    assert [link.get_type() for link in network.links()] == ["CVPIPE", "PIPE", "PUMP", "PRV"]
    assert network.links()[0].get_vertices() == [(0.5, 0.5)]


def test_epanet_import_skips_link_geometry_when_nodes_are_missing(tmp_path):
    inp = tmp_path / "missing_nodes.inp"
    inp.write_text(
        textwrap.dedent(
            """
            [JUNCTIONS]
            J1 0
            [COORDINATES]
            J1 0 0
            [PIPES]
            P1 J1 MISSING 1.0 100 120 0 Open
            [VERTICES]
            P1 0.5 0.5
            [END]
            """
        ).strip(),
        encoding="latin-1",
    )

    network = WntNetwork()
    network.from_epanet(inp)

    assert network.links()[0].get_geometry() is None


def test_epanet_export_elevation_truthy_branches(tmp_path):
    network = WntNetwork()
    for name, kind, elevation, x in [
        ("J1", "JUNCTION", 3, 0),
        ("R1", "RESERVOIR", 4, 1),
        ("T1", "TANK", 5, 2),
    ]:
        node = WntNode(name)
        node.set_type(kind)
        node.set_elevation(elevation)
        node.set_geometry((x, 0))
        network.add_node(node)

    link = WntLink("P1", "J1", "R1")
    link.set_geometry([(0, 0), (1, 0)])
    network.add_link(link)

    template = tmp_path / "template.inp"
    output = tmp_path / "output.inp"
    template.write_text(
        "[TITLE]\n[JUNCTIONS]\n[RESERVOIRS]\n[TANKS]\n[PIPES]\n[PUMPS]\n"
        "[VALVES]\n[COORDINATES]\n[VERTICES]\n[BACKDROP]\nKEEP\n[END]\n",
        encoding="latin-1",
    )

    network.to_epanet(output, template)
    text = output.read_text(encoding="latin-1")

    assert "J1    3.0    0.0" in text
    assert "R1    4.0" in text
    assert "T1    5.0" in text
    assert "KEEP" in text


def test_epanet_export_reservoir_without_elevation(tmp_path):
    network = WntNetwork()
    reservoir = WntNode("R0")
    reservoir.set_type("RESERVOIR")
    reservoir.set_geometry((0, 0))
    network.add_node(reservoir)

    template = tmp_path / "template.inp"
    output = tmp_path / "output.inp"
    template.write_text(
        "[TITLE]\n[JUNCTIONS]\n[RESERVOIRS]\n[TANKS]\n[PIPES]\n[PUMPS]\n"
        "[VALVES]\n[COORDINATES]\n[VERTICES]\n[BACKDROP]\n[END]\n",
        encoding="latin-1",
    )

    network.to_epanet(output, template)

    assert "R0    0.0" in output.read_text(encoding="latin-1")


def test_validate_reports_link_with_undefined_start_node():
    network = WntNetwork()
    node = WntNode("J1")
    node.set_geometry((0, 0))
    network.add_node(node)
    link = WntLink("P1", "MISSING", "J1")
    link.set_geometry([(1, 0), (0, 0)])
    network.add_link(link)

    assert network.validate()["undefined node links"] == {"P1"}


def test_graph_classifies_tree_and_mesh_edges():
    graph = Graph()
    graph.add_edge("T1", "A", "B")
    graph.add_edge("T2", "B", "C")
    graph.add_edge("M1", "D", "E")
    graph.add_edge("M2", "E", "F")
    graph.add_edge("M3", "F", "D")

    assert set(graph.get_nodes()) == {"A", "B", "C", "D", "E", "F"}
    assert graph.node_count() == 6
    assert graph.edge_count() == 5
    assert graph.get_incident_edges("B") == {"T1", "T2"}
    assert graph.get_contiguous_edges("T1") == {"T2"}
    assert graph.get_degrees()["B"] == 2
    assert graph.classify() == {
        "T1": ("BRANCHED", 1),
        "T2": ("BRANCHED", 1),
        "M1": ("MESHED", 1),
        "M2": ("MESHED", 1),
        "M3": ("MESHED", 1),
    }

    with pytest.raises(NameError, match="exists"):
        graph.add_edge("T1", "X", "Y")

    fresh = Graph()
    fresh.add_edge("M1", "A", "B")
    fresh.add_edge("M2", "B", "C")
    fresh.add_edge("M3", "C", "A")
    assert fresh.classify() == {
        "M1": ("MESHED", 1),
        "M2": ("MESHED", 1),
        "M3": ("MESHED", 1),
    }


def test_tin_triangle_and_landxml_loading(tmp_path):
    triangle = Triangle((0, 0, 1), (1, 0, 2), (0, 1, 3))

    assert triangle.xy_area() == 0.5
    assert triangle.is_inside((0.25, 0.25))
    assert not triangle.is_inside((2, 2))
    assert triangle.z((0.25, 0.25)) == pytest.approx(1.75)

    xml = tmp_path / "surface.xml"
    xml.write_text(
        textwrap.dedent(
            """
            <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
              <Surfaces>
                <Surface name="Ground">
                  <Definition surfType="TIN">
                    <Pnts>
                      <P id="1">0 0 1</P>
                      <P id="2">0 1 2</P>
                      <P id="3">1 0 3</P>
                    </Pnts>
                    <Faces><F>1 2 3</F></Faces>
                  </Definition>
                  <Metadata />
                </Surface>
              </Surfaces>
            </LandXML>
            """
        ).strip(),
        encoding="utf-8",
    )

    tin = TIN()
    tin.from_landxml(xml, "Ground")

    assert tin.elevations([(0.25, 0.25), (5, 5)]) == [pytest.approx(1.75), None]

    with pytest.raises(Exception, match="Incorrect name"):
        TIN().from_landxml(xml, "Missing")


def test_tin_reload_replaces_previous_surface(tmp_path):
    xml = tmp_path / "surfaces.xml"
    xml.write_text(
        textwrap.dedent(
            """
            <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
              <Surfaces>
                <Surface name="Ground">
                  <Definition surfType="TIN">
                    <Pnts>
                      <P id="1">0 0 1</P>
                      <P id="2">0 1 2</P>
                      <P id="3">1 0 3</P>
                    </Pnts>
                    <Faces><F>1 2 3</F></Faces>
                  </Definition>
                </Surface>
                <Surface name="Roof">
                  <Definition surfType="TIN">
                    <Pnts>
                      <P id="1">0 0 10</P>
                      <P id="2">0 1 20</P>
                      <P id="3">1 0 30</P>
                    </Pnts>
                    <Faces><F>1 2 3</F></Faces>
                  </Definition>
                </Surface>
              </Surfaces>
            </LandXML>
            """
        ).strip(),
        encoding="utf-8",
    )

    tin = TIN()
    tin.from_landxml(xml, "Ground")
    assert tin.elevations([(0.25, 0.25)]) == [pytest.approx(1.75)]

    tin.from_landxml(xml, "Roof")
    assert tin.elevations([(0.25, 0.25)]) == [pytest.approx(17.5)]


def test_tin_rejects_degenerate_faces(tmp_path):
    xml = tmp_path / "surface.xml"
    xml.write_text(
        textwrap.dedent(
            """
            <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
              <Surfaces>
                <Surface name="FlatLine">
                  <Definition surfType="TIN">
                    <Pnts>
                      <P id="1">0 0 1</P>
                      <P id="2">1 1 2</P>
                      <P id="3">2 2 3</P>
                    </Pnts>
                    <Faces><F>1 2 3</F></Faces>
                  </Definition>
                </Surface>
              </Surfaces>
            </LandXML>
            """
        ).strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="non-zero XY area"):
        TIN().from_landxml(xml, "FlatLine")


def test_tin_spatial_index_limits_candidate_triangles(tmp_path):
    xml = tmp_path / "surface.xml"
    xml.write_text(
        textwrap.dedent(
            """
            <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
              <Surfaces>
                <Surface name="Ground">
                  <Definition surfType="TIN">
                    <Pnts>
                      <P id="1">100 100 0</P>
                      <P id="2">100 101 0</P>
                      <P id="3">101 100 0</P>
                      <P id="4">0 0 10</P>
                      <P id="5">0 1 20</P>
                      <P id="6">1 0 30</P>
                    </Pnts>
                    <Faces>
                      <F>1 2 3</F>
                      <F>4 5 6</F>
                    </Faces>
                  </Definition>
                </Surface>
              </Surfaces>
            </LandXML>
            """
        ).strip(),
        encoding="utf-8",
    )

    tin = TIN()
    tin.from_landxml(xml, "Ground")

    def fail_if_checked(point):
        raise AssertionError(f"Far triangle should not be checked for {point}")

    tin._triangles[0].is_inside = fail_if_checked

    assert tin.elevations([(0.25, 0.25)]) == [pytest.approx(17.5)]


def test_landxml_pipe_network_parser(tmp_path):
    xml = tmp_path / "network.xml"
    xml.write_text(
        textwrap.dedent(
            """
            <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
              <CoordinateSystem epsgCode="EPSG:25830" />
              <PipeNetworks>
                <PipeNetwork name="Storm" pipeNetType="storm">
                  <Struct name="S1" desc="Inlet" elevSump="1" elevRim="3">
                    <Center>10 20</Center>
                    <Invert refPipe="P1" elev="1.5" />
                  </Struct>
                  <Struct name="S2" desc="Outlet" elevSump="2" elevRim="5">
                    <Center>11 21</Center>
                    <Invert refPipe="P1" elev="2.5" />
                  </Struct>
                  <Struct name="D1" desc="Dummy Null Structure for LandXML purposes" elevSump="0" elevRim="0" />
                  <Pipe name="P1" refStart="S1" refEnd="S2" length="12.3456" slope="0.012345">
                    <CircPipe diameter="300" />
                  </Pipe>
                </PipeNetwork>
              </PipeNetworks>
            </LandXML>
            """
        ).strip(),
        encoding="utf-8",
    )

    data = network_from_xml(xml)
    storm = data["networks"]["Storm"]

    assert data["epsg_code"] == "EPSG:25830"
    assert storm["nodes"]["S1"]["x"] == 20
    assert storm["nodes"]["S1"]["depth"] == 2
    assert storm["links"]["P1"]["length"] == 12.346
    assert storm["links"]["P1"]["slope"] == 0.0123
    assert storm["links"]["P1"]["section"] == "300"

    xml.write_text(
        textwrap.dedent(
            """
            <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
              <CoordinateSystem ogcWktCode="LOCAL_CS[]" />
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
                  <RectPipe width="2" height="3" />
                </Pipe>
              </PipeNetwork>
            </LandXML>
            """
        ).strip(),
        encoding="utf-8",
    )

    data = network_from_xml(xml)
    assert data["wkt_crs"] == "LOCAL_CS[]"
    assert data["networks"]["Storm"]["links"]["P1"]["section"] == "2X3"

    xml.write_text(
        """
        <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
          <CoordinateSystem ogcWktCode="LOCAL_CS[]" />
          <PipeNetwork name="Pressure" pipeNetType="pressure" />
        </LandXML>
        """,
        encoding="utf-8",
    )
    with pytest.raises(NotImplementedError, match="Pressurized"):
        network_from_xml(xml)


def test_landxml_parser_handles_optional_crs_desc_and_inverts(tmp_path):
    xml = tmp_path / "network.xml"
    xml.write_text(
        textwrap.dedent(
            """
            <LandXML xmlns="http://www.landxml.org/schema/LandXML-1.2">
              <PipeNetwork name="Storm" pipeNetType="storm">
                <Struct name="S1" elevSump="1" elevRim="3">
                  <Center>10 20</Center>
                  <Invert refPipe="P1" elev="1.5" />
                </Struct>
                <Struct name="S2" elevSump="2" elevRim="5">
                  <Center>11 21</Center>
                  <Invert refPipe="P1" elev="2.5" />
                </Struct>
                <Struct name="S3" elevSump="2" elevRim="5">
                  <Center>12 22</Center>
                </Struct>
                <Pipe name="P1" refStart="S1" refEnd="S2" length="12">
                  <CircPipe diameter="300" />
                </Pipe>
                <Pipe name="P2" refStart="S2" refEnd="S3" length="8">
                  <CircPipe diameter="200" />
                </Pipe>
              </PipeNetwork>
            </LandXML>
            """
        ).strip(),
        encoding="utf-8",
    )

    data = network_from_xml(xml)
    storm = data["networks"]["Storm"]

    assert "epsg_code" not in data
    assert "wkt_crs" not in data
    assert set(storm["nodes"]) == {"S1", "S2", "S3"}
    assert set(storm["links"]) == {"P1"}
    assert storm["links"]["P1"]["slope"] == 0
