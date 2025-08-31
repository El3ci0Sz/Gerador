# mapping_generator_CGRA_Grammar.py

from src.cgra.interconnection import Interconnection
from src.mapping_utils.grammar import Grammar

class Mapping_generator_CGRA_Grammar:
    # MUDANÇA: Construtor atualizado para receber 'recipe'
    def __init__(self, cgra_dim: tuple, II: int, bits: str, num_nodes: int, recipe: dict, k_range: tuple, no_extend_io: bool, max_path_length: int):
        self.cgra_dim = cgra_dim
        self.II = II
        self.bits = bits
        self.num_nodes = num_nodes
        self.recipe = recipe # Novo
        self.k_range = k_range
        self.no_extend_io = no_extend_io
        self.max_path_length = max_path_length
        
        self.interconnection_module = Interconnection(self.cgra_dim, self.bits, self.II)
        self.border_nodes = self.interconnection_module.get_border_nodes()
        self.architecture_graph = self.interconnection_module.get_interconnections()

    def _create_cgra_fabric_graph(self):
        return self.interconnection_module.get_interconnections()

    def mapp(self, max_attempts=10):
        """Tenta gerar um mapeamento válido usando a classe Grammar."""
        for attempt in range(max_attempts):
            print(f"  - Tentativa de geração com Gramática {attempt+1}/{max_attempts} para alvo de {self.num_nodes} nós.")
            
            # MUDANÇA: Passa 'recipe' para a gramática
            grammar = Grammar(
                architecture_graph=self.architecture_graph,
                border_nodes=self.border_nodes,
                grid_dim=self.cgra_dim,
                target_size=self.num_nodes,
                recipe=self.recipe,
                k_range=self.k_range,
                max_path_length=self.max_path_length,
                no_extend_io=self.no_extend_io
            )
            
            final_mapping = grammar.generate()

            # A validação agora ocorre dentro da Grammar, que retorna None em caso de falha.
            if final_mapping:
                return final_mapping
        
        return None
