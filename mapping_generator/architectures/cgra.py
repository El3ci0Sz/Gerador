# mapping_generator/architectures/cgra.py

import networkx as nx

class CgraArch:
    """Generates the connectivity graph for a CGRA.
    
    This class builds a directed graph representing all possible connections
    in a CGRA for a given size, Initiation Interval (II), and interconnection
    scheme defined by a 4-bit string.
    """

    def __init__(self, dimensions: tuple, interconnect_bits: str, ii: int = 1):
        """Initializes the CGRA architecture.

        Args:
            dimensions (tuple): The (rows, cols) dimensions of the CGRA grid.
            interconnect_bits (str): A 4-bit string "mdht" representing:
                                     'm': mesh 
                                     'd': diagonal 
                                     'h': one-hop 
                                     't': toroidal 
            ii (int): The Initiation Interval, representing the time dimension.
        """
        self.rows, self.cols = dimensions
        self.bits = interconnect_bits
        self.ii = ii
        self.graph = self._create_base_grid_with_ii()
        self._add_interconnections()

    def get_graph(self) -> nx.DiGraph:
        """Returns the generated CGRA connectivity graph."""
        return self.graph

    def _create_base_grid_with_ii(self) -> nx.DiGraph:
        """Creates a grid graph with nodes representing PEs at time steps."""
        graph = nx.DiGraph()
        for t in range(self.ii):
            for r in range(self.rows):
                for c in range(self.cols):
                    graph.add_node((r, c, t))
        return graph

    def _add_interconnections(self):
        """Adds all configured connections for every node in the graph."""
        mesh, diagonal, one_hop, toroidal = [bool(int(b)) for b in self.bits]
        
        for t in range(self.ii):
            for r in range(self.rows):
                for c in range(self.cols):
                    source_node = (r, c, t)
                    self._add_temporal_connections(source_node)
                    self._add_spatial_connections(source_node, mesh, diagonal, one_hop)

                    self._add_toroidal_connections(source_node, toroidal)

    def _add_temporal_connections(self, source_node: tuple):
        """Adds edges from a node to itself in the next time step for pipelining."""
        if self.ii > 1:
            r, c, t = source_node
            target_time_node = (r, c, (t + 1) % self.ii)
            self.graph.add_edge(source_node, target_time_node)

    def _add_spatial_connections(self, source_node: tuple, mesh: bool, diagonal: bool, one_hop: bool):
        """Adds standard spatial connections (mesh, diagonal, one-hop) from a source node."""
        r, c, t = source_node
        potential_neighbors = []
        if mesh:
            potential_neighbors.extend([(r+1, c), (r-1, c), (r, c+1), (r, c-1)])
        if diagonal:
            potential_neighbors.extend([(r+1, c+1), (r+1, c-1), (r-1, c+1), (r-1, c-1)])
        if one_hop:
            potential_neighbors.extend([(r+2, c), (r-2, c), (r, c+2), (r, c-2)])
        
        for nr, nc in potential_neighbors:
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                self.graph.add_edge(source_node, (nr, nc, t))

    def _add_toroidal_connections(self, source_node: tuple, toroidal: bool):
        """Adds toroidal (wrap-around) connections from a source node."""
        if not toroidal:
            return
            
        r, c, t = source_node
        tor_neighbors = [
            ((r + 1) % self.rows, c), 
            ((r - 1 + self.rows) % self.rows, c), 
            (r, (c + 1) % self.cols), 
            (r, (c - 1 + self.cols) % self.cols)
        ]
        for nr, nc in tor_neighbors:
            target_node = (nr, nc, t)
            if not self.graph.has_edge(source_node, target_node):
                self.graph.add_edge(source_node, target_node)
    
    def get_border_nodes(self) -> set:
        """Returns a set of all nodes on the physical border of the CGRA.
        
        Returns:
            set: A set of (row, col, time) tuples representing border nodes.
        """
        borders = set()
        for t in range(self.ii):
            for r in range(self.rows):
                for c in range(self.cols):
                    if r == 0 or r == self.rows - 1 or c == 0 or c == self.cols - 1:
                        borders.add((r, c, t))
        return borders
