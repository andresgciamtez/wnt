"""Regression tests for core network utilities."""

import pytest

from wnt.utils.utils_core import WntLink, WntNetwork, WntNode, net_from_linestrings
from wnt.utils.utils_graph import node_degrees


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
    network = WntNetwork()
    network.add_node(WntNode("N1"))
    network.add_link(WntLink("L1", "N1", "MISSING"))

    assert node_degrees(network) == {"N1": 1, "MISSING": 1}


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


