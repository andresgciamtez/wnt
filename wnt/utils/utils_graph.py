"""Graph utilities for network topology analysis."""

from collections import defaultdict, deque


def graph_from_records(node_ids, links, path):
    """Export validated topology records to Trivial Graph Format (TGF)."""
    node_ids = list(node_ids)
    links = list(links)
    node_index = {}
    for index, node_id in enumerate(node_ids):
        node_index.setdefault(node_id, index)
    undefined = [
        link_id for link_id, start_id, end_id in links
        if start_id not in node_index or end_id not in node_index
    ]
    if undefined:
        raise ValueError("Links reference undefined nodes: " + ", ".join(map(str, undefined)))

    with open(path, 'w', encoding='utf-8') as graph_file:
        for index, node_id in enumerate(node_ids):
            graph_file.write('{} {} \n'.format(index, node_id))
        graph_file.write('# \n')
        for link_id, start_id, end_id in links:
            graph_file.write('{} {} {} \n'.format(
                node_index[start_id], node_index[end_id], link_id
            ))


def node_degrees_from_records(node_ids, links):
    """Return node degrees from node IDs and link records."""
    degrees = {}

    for node_id in node_ids:
        degrees[node_id] = 0
    for _, start_id, end_id in links:
        for link_end in (start_id, end_id):
            if link_end not in degrees:
                degrees[link_end] = 0
            degrees[link_end] += 1
    return degrees


def validate_records(node_ids, links):
    """Return topology problems from node IDs and link records."""
    problems = {
        'orphan nodes': set(),
        'duplicate nodes': set(),
        'undefined node links': set(),
        'duplicate links': set(),
        'loops': set()
    }

    seen_nodes = set()
    for node_id in node_ids:
        if node_id in seen_nodes:
            problems['duplicate nodes'].add(node_id)
        seen_nodes.add(node_id)
        problems['orphan nodes'].add(node_id)

    seen_links = set()
    for link_id, start_name, end_name in links:
        if link_id in seen_links:
            problems['duplicate links'].add(link_id)
        seen_links.add(link_id)

        problems['orphan nodes'].discard(start_name)
        problems['orphan nodes'].discard(end_name)

        if start_name not in seen_nodes or end_name not in seen_nodes:
            problems['undefined node links'].add(link_id)

        if start_name == end_name:
            problems['loops'].add(link_id)

    return problems


def unique_zone_classification(classified):
    """Return classified links with zone numbers unique across all topology classes."""
    zone_keys = sorted(
        set(classified.values()),
        key=lambda value: (0 if value[0] == 'BRANCHED' else 1, value[1]),
    )
    zone_by_key = {key: index for index, key in enumerate(zone_keys, start=1)}
    return {
        link_id: (topology, zone_by_key[(topology, zone)])
        for link_id, (topology, zone) in classified.items()
    }


class Graph():
    """Define a graph as a dictionary of edges, {label: (start, end)}.
    """
    def __init__(self):
        self.edges = {}
        self._nodes = set()
        self._updated = False
        self._degrees = {}
        self._incident = defaultdict(set)


    def add_edge(self, label, start, end):
        """Add a edge to the graph"""
        if label not in self.edges:
            self.edges[label] = (start, end)
            self._nodes.add(start)
            self._nodes.add(end)
            self._incident[start].add(label)
            self._incident[end].add(label)
            self._updated = False
        else:
            msg = 'Edge: {} exists!'.format(label)
            raise NameError(msg)

    def get_nodes(self):
        """Return the graph nodes"""
        return list(self._nodes)

    def get_incident_edges(self, nodelabel):
        """Return the incident edge labels to a node."""
        return set(self._incident.get(nodelabel, ()))

    def get_contiguous_edges(self, label):
        """Return labels of edges sharing an endpoint with an edge."""
        contiguous = set()
        for node in self.edges[label]:
            contiguous.update(self._incident.get(node, ()))
        contiguous.discard(label)
        return contiguous

    def node_count(self):
        """Return the graph node number"""
        return len(self._nodes)

    def edge_count(self):
        """Return the graph edge number"""
        return len(self.edges)

    def calculate_degrees(self):
        """Calculate the node degrees of the graph"""
        self._degrees = {}
        for value in self.edges.values():
            for node in value:
                if node in self._degrees.keys():
                    self._degrees[node] += 1
                else:
                    self._degrees[node] = 1
        self._updated = True

    def get_degrees(self):
        """Return a dict, key: node label and value: node degree"""
        if not self._updated:
            self.calculate_degrees()
        return self._degrees

    def classify(self):
        """Classify edges as branched trees or meshed two-core components."""
        incident = {node: set(labels) for node, labels in self._incident.items()}
        degrees = {node: 0 for node in self._nodes}
        for start, end in self.edges.values():
            degrees[start] += 1
            degrees[end] += 1

        queue = deque(node for node, degree in degrees.items() if degree == 1)
        branched = set()
        while queue:
            node = queue.popleft()
            if degrees[node] != 1:
                continue
            for label in tuple(incident.get(node, ())):
                if label in branched:
                    continue
                branched.add(label)
                for endpoint in self.edges[label]:
                    incident[endpoint].discard(label)
                    degrees[endpoint] -= 1
                    if degrees[endpoint] == 1:
                        queue.append(endpoint)

        meshed = set(self.edges) - branched

        def components(labels):
            remaining = set(labels)
            groups = []
            while remaining:
                seed = min(remaining, key=str)
                remaining.remove(seed)
                component = {seed}
                pending = [seed]
                while pending:
                    label = pending.pop()
                    for endpoint in self.edges[label]:
                        neighbors = self._incident.get(endpoint, set()) & remaining
                        remaining.difference_update(neighbors)
                        component.update(neighbors)
                        pending.extend(neighbors)
                groups.append(component)
            return groups

        classified = {}
        for topology, labels in (("BRANCHED", branched), ("MESHED", meshed)):
            for zone, component in enumerate(components(labels), start=1):
                for label in component:
                    classified[label] = (topology, zone)
        return classified
