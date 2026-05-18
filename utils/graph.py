"""Graph utilities for network topology analysis."""

class Graph():
    """Define a graph as a dictionary of edges, {label: (start, end)}.
    """
    def __init__(self):
        self.edges = {}
        self._nodes = set()
        self._updated = False
        self._degrees = {}


    def add_edge(self, label, start, end):
        """Add a edge to the graph"""
        if label not in self.edges:
            self.edges[label] = (start, end)
            self._nodes.add(start)
            self._nodes.add(end)
            self._updated = False
        else:
            msg = 'Edge: {} exists!'.format(label)
            raise NameError(msg)

    def get_nodes(self):
        """Return the graph nodes"""
        return list(self._nodes)

    def get_incident_edges(self, nodelabel):
        """Return the incident edge labels to a node"""
        incidentedges = set()
        for key, value in self.edges.items():
            if nodelabel in value:
                incidentedges.add(key)
        return incidentedges

    def get_contiguous_edges(self, label):
        """Return the contiguous edges labels to another"""
        contiguous = set()
        for n in self.edges[label][:]:
            for e in self.get_incident_edges(n):
                if e != label:
                    contiguous.add(e)
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
        '''Return subgraphs enumerating trees and meshes'''

        # BRANCHED AND MESHED
        branched = set()
        if not self._updated:
            self.calculate_degrees()
        self._updated = False
        while 1 in self._degrees.values():
            self._degrees.keys()
            for key, value in self._degrees.items():
                if value == 1:
                    for label in self.get_incident_edges(key):
                        branched.add(label)
                        for node in self.edges[label][:]:
                            self._degrees[node] -= 1
        meshed = set()
        for label in self.edges:
            if label not in branched:
                meshed.add(label)

        # SEPARATE TREES AND MESH
        trees = {}
        meshes = {}
        for graphtype in ['TREE', 'MESH']:
            cnt = 0
            if graphtype == 'TREE':
                initial = branched
            else:
                initial = meshed
            while initial:
                cnt += 1
                pre = set()
                new = set()
                sub = set()
                pre.add(initial.pop())
                while pre:
                    sub.update(pre)
                    for e in pre:
                        for ce in self.get_contiguous_edges(e):
                            if ce in initial:
                                initial.discard(ce)
                                new.add(ce)
                    sub.update(new)
                    pre = new.copy()
                    new = set()
                if graphtype == 'TREE':
                    trees[cnt] = sub
                else:
                    meshes[cnt] = sub

        # RECLASSIFY
        classified = {}
        for graphtype in ['BRANCHED', 'MESHED']:
            if graphtype == 'BRANCHED':
                g = trees
            else:
                g = meshes
            for key, value in g.items():
                for label in value:
                    classified[label] = (graphtype, key)
        return classified


