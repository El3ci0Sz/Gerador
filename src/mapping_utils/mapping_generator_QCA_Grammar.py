from src.qca.qca import QCA
from src.mapping_utils.grammar import Grammar
import networkx as nx
import random

class Mapping_generator_QCA:
    def __init__(self, grid_dim: tuple, qca_arch_type: str, grammar_steps: int, k_range: list, no_extend_io: bool, max_path_length: int, balance_paths: bool):
        self.grid_dim = grid_dim
        self.qca_arch_type = qca_arch_type
        self.grammar_steps = grammar_steps
        self.k_range = k_range
        self.no_extend_io = no_extend_io
        self.max_path_length = max_path_length
        self.balance_paths = balance_paths

        fabric_generator = QCA(self.grid_dim, self.qca_arch_type)
        self.architecture_graph = fabric_generator.get_graph()
        self.border_nodes = fabric_generator.get_border_nodes()

    def mapp(self, max_attempts=10, min_nodes=5):
        for attempt in range(max_attempts):
            target_node_count = self.grammar_steps 
            default_recipe = {"reconvergence": 0, "convergence": 0}
            grammar = Grammar(
                architecture_graph=self.architecture_graph,
                border_nodes=self.border_nodes,
                grid_dim=self.grid_dim,
                target_size=target_node_count,
                recipe=default_recipe,        
                k_range=self.k_range,
                max_path_length=self.max_path_length,
                no_extend_io=self.no_extend_io
            )
            
            grammar.placement_graph.add_node(random.choice(list(self.architecture_graph.nodes())))
            grammar.used_nodes = set(grammar.placement_graph.nodes())
            
            for _ in range(self.grammar_steps -1): 
                if not grammar.generate_pattern():
                    break 

            grammar.merge()
            
            if not self.no_extend_io:
                grammar.synchronize_io_and_extend_to_border()
            
            final_mapping = grammar.placement_graph

            if len(final_mapping.nodes) >= min_nodes:
                return final_mapping
        
        raise ValueError(f"Não foi possível gerar um mapeamento com pelo menos {min_nodes} nós após {max_attempts} tentativas.")
