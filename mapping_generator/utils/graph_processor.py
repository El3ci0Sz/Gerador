# mapping_generator/utils/graph_processor.py

import networkx as nx
from .mapping import Mapping

class GraphProcessor:
    """Provides utility functions for processing and validating mappings."""

    def __init__(self, mapping: Mapping):
        """Initializes the processor with a mapping object.

        Args:
            mapping (Mapping): The mapping to be processed.
        """
        self.mapping = mapping
        self.dfg = self._build_dfg_from_mapping()

    def _build_dfg_from_mapping(self) -> nx.DiGraph:
        """Constructs a NetworkX DiGraph from the mapping's routing information."""
        dfg = nx.DiGraph()
        nodes = list(self.mapping.placement.keys())
        dfg.add_nodes_from(nodes)
        
        for (source_id, dest_id), path in self.mapping.routing.items():
            if source_id in nodes and dest_id in nodes:
                dfg.add_edge(source_id, dest_id)
        return dfg

    def is_valid(self) -> bool:
        """Checks if the generated DFG is valid (e.g., is connected).

        Returns:
            bool: True if the graph is valid, False otherwise.
        """
        if self.dfg.number_of_nodes() == 0:
            return False
        
        # A simple validation check: ensure the graph is weakly connected.
        # More complex validation rules could be added here.
        return nx.is_weakly_connected(self.dfg)
