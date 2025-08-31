# mapping_generator/generation/random_cgra_generator.py

import random
import networkx as nx
from ..architectures.cgra import CgraArch
from ..utils.mapping import Mapping
from ..utils.graph_processor import GraphProcessor

class RandomCgraGenerator:
    """Generates a random valid mapping of a DFG to a CGRA."""

    def __init__(self, dfg_size: int, II: int, cgra_dim: tuple, bits: str, 
                 alpha: float = 0.8, alpha2: float = 0.4):
        """Initializes the random generator.

        Args:
            dfg_size (int): The number of nodes in the DFG to generate.
            II (int): The initiation interval for the mapping.
            cgra_dim (tuple): The (rows, cols) dimensions of the CGRA.
            bits (str): The 4-bit string defining the CGRA interconnect.
            alpha (float): Probability of adding extra connections during routing.
            alpha2 (float): Probability of removing existing connections during routing.
        """
        self.dfg_size = dfg_size
        self.II = II
        self.cgra_dim = cgra_dim
        self.bits = bits
        self.alpha = alpha
        self.alpha2 = alpha2
        
        cgra_architecture = CgraArch(self.cgra_dim, self.bits, self.II)
        self.cgra_graph = cgra_architecture.get_graph()

    def generate_mapping(self, max_attempts: int = 1000) -> Mapping | None:
        """Attempts to generate a valid (placement + routing) mapping.

        Args:
            max_attempts (int): Max number of tries before giving up.

        Returns:
            Mapping | None: A valid Mapping object or None if generation fails.
        """
        for _ in range(max_attempts):
            mapping = Mapping(self.dfg_size)
            self._perform_placement(mapping)
            self._perform_routing(mapping)
            
            if GraphProcessor(mapping).is_valid():
                return mapping
        
        raise ValueError(f"Failed to find a valid mapping after {max_attempts} attempts.")

    def _perform_placement(self, mapping: Mapping):
        """Performs a random placement of DFG nodes onto the CGRA grid."""
        nodes = list(range(self.dfg_size))
        random.shuffle(nodes)
        
        available_pes = [(r, c, t) for r in range(self.cgra_dim[0]) 
                                   for c in range(self.cgra_dim[1]) 
                                   for t in range(self.II)]
        
        placed_pes = random.sample(available_pes, self.dfg_size)

        for i, node_id in enumerate(nodes):
            mapping.placement[f'op_{node_id}'] = placed_pes[i]

    def _perform_routing(self, mapping: Mapping):
        """Generates random routing between placed nodes."""
        nodes = list(mapping.placement.keys())
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                if i == j: continue
                
                source_id = nodes[i]
                dest_id = nodes[j]
                
                if random.random() < self.alpha:
                    source_pos = mapping.placement[source_id]
                    dest_pos = mapping.placement[dest_id]
                    try:
                        path = nx.shortest_path(self.cgra_graph, source=source_pos, target=dest_pos)
                        mapping.routing[(source_id, dest_id)] = path
                    except (nx.NetworkXNoPath, nx.NodeNotFound):
                        continue
