"""Regression tests for core network utilities."""

import pytest

from wnt.utils.utils_core import WntLink, WntNetwork, WntNode, net_from_linestrings
from wnt.utils.utils_graph import node_degrees_from_records


def test_node_wkt_allows_zero_coordinates():
    """A node placed on either axis still exports valid WKT."""
    node = WntNode("N1")

    node.set_geometry((0, 10))

    assert node.to_wkt() == "Point(0.0 10.0)"


def test_from_epanet_preserves_reservoir_elevation(tmp_path):
    """Reservoir head/elevation is stored when importing an EPANET model."""
    inp_file = tmp_path / "reservoir.inp"
    inp_file.write_text(
        "\n".join(
            [
                "[JUNCTIONS]",
                "[RESERVOIRS]",
                "R1 100.5",
                "[TANKS]",
                "[COORDINATES]",
                "R1 0 0",
                "[PIPES]",
                "[PUMPS]",
                "[VALVES]",
                "[VERTICES]",
                "[END]",
            ]
        ),
        encoding="latin-1",
    )

    network = WntNetwork()
    network.from_epanet(str(inp_file))

    assert network.nodes()[0].get_elevation() == 100.5


def test_from_epanet_allows_missing_optional_sections(tmp_path):
    """Minimal EPANET files do not need every supported section."""
    inp_file = tmp_path / "minimal.inp"
    inp_file.write_text(
        "\n".join(
            [
                "[JUNCTIONS]",
                "J1 10",
                "[COORDINATES]",
                "J1 0 0",
                "[END]",
            ]
        ),
        encoding="latin-1",
    )

    network = WntNetwork()
    network.from_epanet(str(inp_file))

    assert [node.name() for node in network.nodes()] == ["J1"]
    assert network.nodes()[0].get_geometry() == (0.0, 0.0)


def test_label_indexes_preserve_first_duplicate():
    """Label lookups preserve the previous first-match behavior."""
    network = WntNetwork()

    first = WntNode("N1")
    second = WntNode("N1")
    network.add_node(first)
    network.add_node(second)

    first = WntLink("L1", "N1", "N2")
    second = WntLink("L1", "N2", "N3")
    network.add_link(first)
    network.add_link(second)

    assert network.get_nodeindex("N1") == 0
    assert network.get_linkindex("L1") == 0


def test_degree_tolerates_undefined_link_nodes():
    """Degree calculation does not crash before validation reports bad links."""
    links = [("L1", "N1", "MISSING")]

    assert node_degrees_from_records(["N1"], links) == {"N1": 1, "MISSING": 1}


def test_net_from_linestrings_merges_connected_endpoints_with_tolerance():
    """Endpoint clusters are merged through tolerance-based connectivity."""
    nodes, links = net_from_linestrings(
        [
            [(0, 0), (1.00, 0)],
            [(1.04, 0), (2.00, 0)],
            [(1.08, 0), (1.08, 1)],
        ],
        tol=0.05,
    )

    assert len(nodes) == 4
    assert nodes[1] == pytest.approx((1.04, 0.0))
    assert links[0][1] == links[1][0] == links[2][0]


def test_net_from_linestrings_merges_exact_endpoints_without_tolerance():
    """With zero tolerance, only exactly coincident endpoints are merged."""
    nodes, links = net_from_linestrings(
        [[(0, 0), (1, 0)], [(1, 0), (2, 0)]],
        tol=0.0,
    )

    assert nodes == [(0, 0), (1, 0), (2, 0)]
    assert links == [
        [0, 1, [(0, 0), (1, 0)]],
        [1, 2, [(1, 0), (2, 0)]],
    ]


def xml_sample_network(node_prefix="J"):
    network = WntNetwork()
    start = WntNode(f"{node_prefix}1")
    start.set_type("JUNCTION")
    start.set_elevation(1.5)
    start.set_geometry((0, 0))
    start.get_properties("swmm")["invert_elevation"] = 0.25
    start.get_properties("landxml")["origin"] = "Storm"
    network.add_node(start)

    end = WntNode(f"{node_prefix}2")
    end.set_type("OUTFALL")
    end.set_geometry((10, 0))
    network.add_node(end)

    link = WntLink(f"{node_prefix}L1", start.name(), end.name())
    link.set_type("CONDUIT")
    link.set_length(10.0)
    link.set_geometry([(0, 0), (5, 1), (10, 0)])
    link.get_properties("epanet")["roughness"] = 120
    link.get_properties("swmm")["shape"] = "circular"
    link.get_properties("landxml")["geom_shape"] = "circular"
    network.add_link(link)
    return network


def test_wnt_xml_round_trip_preserves_domains_and_metadata(tmp_path):
    xml_file = tmp_path / "network.xml"
    network = xml_sample_network()

    network.to_xml(
        xml_file,
        "v1",
        network_id="demo",
        model_type="swmm",
        crs="EPSG:25830",
        metadata={"source": "unit", "name": "Demo network"},
    )

    loaded = WntNetwork().from_xml(xml_file)

    assert loaded.xml_network_id == "demo"
    assert loaded.xml_version_id == "v1"
    assert loaded.xml_model_type == "swmm"
    assert loaded.xml_crs == "EPSG:25830"
    assert loaded.xml_metadata["source"] == "unit"
    assert [node.name() for node in loaded.nodes()] == ["J1", "J2"]
    assert loaded.nodes()[0].get_properties("swmm") == {"invert_elevation": 0.25}
    assert loaded.nodes()[0].get_properties("landxml") == {"origin": "Storm"}
    assert loaded.links()[0].get_geometry() == [(0.0, 0.0), (5.0, 1.0), (10.0, 0.0)]
    assert loaded.links()[0].get_length() == pytest.approx(10.0)
    assert loaded.links()[0].get_properties("epanet") == {"roughness": 120}
    assert loaded.links()[0].get_properties("swmm") == {"shape": "circular"}


def test_wnt_xml_stores_multiple_versions_and_loads_latest(tmp_path):
    xml_file = tmp_path / "versions.xml"
    first = xml_sample_network("A")
    second = xml_sample_network("B")

    first.to_xml(xml_file, "v1", network_id="demo", metadata={"created": "2026-01-01T00:00:00Z"})
    second.to_xml(xml_file, "v2", network_id="demo", metadata={"created": "2026-01-02T00:00:00Z"})

    loaded = WntNetwork().from_xml(xml_file, version_id="v1", network_id="demo")
    assert [node.name() for node in loaded.nodes()] == ["A1", "A2"]

    latest = WntNetwork().from_xml(xml_file, network_id="demo")
    assert latest.xml_version_id == "v2"
    assert [node.name() for node in latest.nodes()] == ["B1", "B2"]

    with pytest.raises(Exception, match="Network version not found"):
        WntNetwork().from_xml(xml_file, version_id="missing", network_id="demo")


def test_wnt_xml_rejects_links_with_undefined_nodes(tmp_path):
    xml_file = tmp_path / "bad.xml"
    xml_file.write_text(
        """
        <wntNetworkStore schemaVersion="1.0">
          <network id="demo">
            <version id="v1" created="2026-01-01T00:00:00Z" modelType="generic">
              <nodes><node id="N1" type="JUNCTION" x="0" y="0" /></nodes>
              <links>
                <link id="L1" start="N1" end="MISSING" type="PIPE">
                  <vertices><vertex x="0" y="0" /><vertex x="1" y="0" /></vertices>
                </link>
              </links>
            </version>
          </network>
        </wntNetworkStore>
        """,
        encoding="utf-8",
    )

    with pytest.raises(Exception, match="undefined nodes"):
        WntNetwork().from_xml(xml_file)
