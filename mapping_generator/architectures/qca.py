# mapping_generator/architectures/qca.py

import networkx as nx

class QCA:
    """Generates connectivity graphs for QCA architectures.

    This class creates a base graph representing all possible directional
    connections for a given physical QCA architecture and clocking scheme.
    """

    def __init__(self, dimensions: tuple, arch_type: str):
        """Initializes the QCA architecture factory.

        Args:
            dimensions (tuple): The (rows, cols) dimensions of the QCA grid.
            arch_type (str): The clocking scheme type ('U' for USE, 'R' for RES, 
                             'T' for 2DDWave).
        """
        self.dim = dimensions
        self.arch_type = arch_type.upper()
        
        self.USE_CLOCK_TILE = [
            [1, 2, 3, 4],
            [4, 3, 2, 1],
            [3, 4, 1, 2],
            [2, 1, 4, 3]
        ]

        self.RES_CLOCK_TILE = [
            [4, 1, 2, 3],
            [1, 2, 3, 4],
            [2, 3, 4, 1],
            [3, 4, 1, 2]
        ]

    def get_graph(self) -> nx.DiGraph:
        """Gets the generated connectivity graph.

        This is the main public method to retrieve the final architecture graph
        representing all valid connections based on the clocking scheme.

        Returns:
            nx.DiGraph: The directed graph of the QCA architecture.
        """
        return self._generate_connectivity_graph()

    def _generate_connectivity_graph(self) -> nx.DiGraph:
        """Builds the directed graph based on the selected clocking scheme."""
        graph = nx.DiGraph()
        all_nodes = [(r, c) for r in range(self.dim[0]) for c in range(self.dim[1])]

        for node in all_nodes:
            valid_neighbors = set()
            if self.arch_type == "U":
                valid_neighbors = self._get_neighbors_by_clock_flow(node, self._get_use_clock_zone)
            elif self.arch_type == "T":
                valid_neighbors = self._get_neighbors_2ddwave(node)
            elif self.arch_type == "R": 
                valid_neighbors = self._get_neighbors_by_clock_flow(node, self._get_res_clock_zone)
            else:
                raise ValueError(f"Unknown architecture type: {self.arch_type}")

            for neighbor in valid_neighbors:
                graph.add_edge(node, neighbor)
        return graph

    def _is_valid_node(self, node: tuple) -> bool:
        """Checks if a node's coordinates are within the grid boundaries.
        
        Args:
            node (tuple): A tuple representing the (row, col) of the node.

        Returns:
            bool: True if the node is within the grid, False otherwise.
        """
        r, c = node
        return 0 <= r < self.dim[0] and 0 <= c < self.dim[1]
    
    def _get_use_clock_zone(self, node: tuple) -> int:
        """Calculates the clock zone (1-4) for a node in the USE scheme.
        
        Args:
            node (tuple): The (row, col) of the node.

        Returns:
            int: The clock zone number (1-4).
        """
        r, c = node
        return self.USE_CLOCK_TILE[r % 4][c % 4]

    def _get_res_clock_zone(self, node: tuple) -> int:
        """Calculates the clock zone (1-4) for a node in the RES scheme.
        
        Args:
            node (tuple): The (row, col) of the node.

        Returns:
            int: The clock zone number (1-4).
        """
        r, c = node
        return self.RES_CLOCK_TILE[r % 4][c % 4]
    
    def _get_neighbors_by_clock_flow(self, node: tuple, clock_zone_func) -> set:
        """Finds neighbors for directional clocking schemes (USE, RES).

        A connection is valid if a neighbor's clock zone is the successor to the
        source node's clock zone (1->2, 2->3, 3->4, 4->1).

        Args:
            node (tuple): The source node (row, col).
            clock_zone_func (function): The function to use for determining clock zones.

        Returns:
            set: A set of valid neighbor node coordinates.
        """
        r, c = node
        source_zone = clock_zone_func(node)
        target_zone = (source_zone % 4) + 1
        
        potential_neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        
        valid_neighbors = set()
        for neighbor in potential_neighbors:
            if self._is_valid_node(neighbor) and clock_zone_func(neighbor) == target_zone:
                valid_neighbors.add(neighbor)
        return valid_neighbors

    def _get_neighbors_2ddwave(self, node: tuple) -> set:
        """Finds neighbors for the 2DDWave scheme (East and South).
        
        Args:
            node (tuple): The source node (row, col).

        Returns:
            set: A set of valid neighbor node coordinates.
        """
        r, c = node
        potential_neighbors = [(r, c + 1), (r + 1, c)]
        return {n for n in potential_neighbors if self._is_valid_node(n)}

    def get_border_nodes(self) -> set:
        """Returns a set of all node coordinates on the grid's border.
        
        Returns:
            set: A set of (row, col) tuples representing border nodes.
        """
        rows, cols = self.dim
        borders = set()
        for r in range(rows):
            for c in range(cols):
                if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                    borders.add((r, c))
        return borders
