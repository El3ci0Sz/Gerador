
import unittest
import networkx as nx
from collections import defaultdict
import random

# Importe as classes do seu projeto
from src.cgra.interconnection import Interconnection
from src.mapping_utils.grammar import Grammar

def calculate_imbalance_score(graph: nx.DiGraph):
    """ Calcula o 'score de desbalanceamento' de um grafo. """
    if not graph or not nx.is_directed_acyclic_graph(graph):
        print("\n[ANÁLISE] Grafo nulo ou com ciclos. Não é possível calcular o score.")
        return -1

    levels = {}
    try:
        for node in nx.topological_sort(graph):
            level = 0
            for pred in graph.predecessors(node):
                level = max(level, levels.get(pred, -1) + 1)
            levels[node] = level
    except nx.NetworkXUnfeasible:
        return -1

    total_imbalance = 0
    nodes_with_multiple_inputs = [n for n, d in graph.in_degree() if d > 1]
    
    print("\n--- ANÁLISE DE BALANCEAMENTO ---")
    for node in nodes_with_multiple_inputs:
        predecessor_levels = sorted([levels.get(p) for p in graph.predecessors(node)])
        if len(set(predecessor_levels)) > 1:
            imbalance = max(predecessor_levels) - min(predecessor_levels)
            total_imbalance += imbalance
            print(f"  [DESBALANCEAMENTO] Nó {node} (Nível {levels.get(node)}) recebe de níveis {predecessor_levels}. Imbalance: {imbalance}")

    if total_imbalance == 0:
        print("  [RESULTADO] O grafo é PERFEITAMENTE BALANCEADO.")
    
    return total_imbalance

def visualize_placement(used_nodes, grid_dim, II):
    """ Desenha uma representação textual do mapeamento no console. """
    print("\n--- VISUALIZAÇÃO DO MAPEAMENTO FÍSICO ---")
    for t in range(II):
        print(f"--- Tempo (t) = {t} ---")
        grid = [['[ . ]' for _ in range(grid_dim[1])] for _ in range(grid_dim[0])]
        for node in used_nodes:
            if node[2] == t:
                grid[node[0]][node[1]] = '[ U ]'
        for row in grid:
            print(" ".join(row))
    print("---------------------------------")

class TestBalanceDebugger(unittest.TestCase):
    
    def test_single_complex_generation(self):
        """
        Executa uma única geração com todas as regras habilitadas para
        produzir um log de depuração detalhado.
        """
        # --- Configurações do Teste ---
        random.seed(42) # Seed fixa para reprodutibilidade
        target_size = 20
        grid_dim = (4, 4)
        II = 3
        bits = "1100" # Malha + Diagonal
        rule_flags = "111" # Habilita todas as regras
        
        # --- Setup da Arquitetura ---
        interconn = Interconnection(grid_dim, bits, II)
        arch_graph = interconn.get_interconnections()
        
        # --- Geração ---
        grammar = Grammar(
            architecture_graph=arch_graph, border_nodes=set(),
            grid_dim=grid_dim, target_size=target_size, rule_flags=rule_flags,
            k_range=(2, 3), max_path_length=20, no_extend_io=True
        )
        final_graph = grammar.generate()
        
        # --- Análise e Visualização ---
        self.assertIsNotNone(final_graph, "O gerador não conseguiu criar um grafo.")
        
        visualize_placement(final_graph.nodes(), grid_dim, II)
        
        score = calculate_imbalance_score(final_graph)
        print(f"\nSCORE FINAL DE DESBALANCEAMENTO: {score}")

if __name__ == '__main__':
    unittest.main(verbosity=2)
