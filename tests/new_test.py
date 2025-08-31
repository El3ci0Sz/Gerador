
import unittest
from src.utils.Mapping import Mapping
from src.utils.graph_processing import Graph_Processing
from src.utils.interconnection import Interconnection
from src.utils.routing import Routing
import pprint

class TestGraphProcessingAndInterconnection(unittest.TestCase):

    def setUp(self):
        # Número de vértices no grafo DFG
        self.dfg_vertices = 3
        self.mapping = Mapping(self.dfg_vertices)

        # Define arestas do grafo
        self.mapping.dfg_edges = {
            0: [1],
            1: [2],
            2: []
        }

        # Define placement manual dos nós
        self.mapping.placement = {
            0: (0, 0, 0),
            1: (0, 1, 0),
            2: (1, 1, 0)
        }

        # Parâmetros gerais
        self.dfg_tam = self.dfg_vertices
        self.cgra_dim = (2, 2)
        self.II = 2  # Instruction Interval

    def test_graph_processing_valid(self):
        print("\n=== Teste GraphProcessing.is_valid ===")
        processor = Graph_Processing(self.mapping, self.dfg_tam)
        is_valid = processor.is_valid()
        print("DFG é válido?", is_valid)
        self.assertTrue(is_valid)

    def test_interconnection_mesh(self):
        print("\n=== Teste Interconnection (mesh) ===")
        inter = Interconnection(self.cgra_dim, '1000', self.mapping, self.II)
        neighbors = inter.neighbor_dict

        for node, pos in self.mapping.placement.items():
            r, c, t = pos
            next_t = (t + 1) % self.II
            expected_neighbors = set()

            if r > 0:
                expected_neighbors.add((r-1, c, next_t))
            if r < self.cgra_dim[0] - 1:
                expected_neighbors.add((r+1, c, next_t))
            if c > 0:
                expected_neighbors.add((r, c-1, next_t))
            if c < self.cgra_dim[1] - 1:
                expected_neighbors.add((r, c+1, next_t))
            expected_neighbors.add((r, c, next_t))

            self.assertSetEqual(set(neighbors[node]), expected_neighbors)

        print("Dicionário de vizinhos (mesh):")
        pprint.pprint(neighbors)

    def test_routing_mesh(self):
        print("\n=== Teste Routing (com interconexão mesh) ===")
        inter = Interconnection(self.cgra_dim, '1000', self.mapping, self.II)
        try:
            Routing(self.mapping, self.dfg_tam, 0.9, 0.3, inter.neighbor_dict)
            routing_success = True
        except Exception as e:
            print(f"Routing failed: {e}")
            routing_success = False

        print("Roteamento realizado com sucesso?", routing_success)
        print("Resultado do dicionário de roteamento:")
        pprint.pprint(self.mapping.routing)

        self.assertTrue(routing_success)

if __name__ == '__main__':
    unittest.main()
