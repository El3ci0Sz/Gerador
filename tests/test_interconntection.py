import unittest
from src.utils.Mapping import Mapping
from src.utils.interconnection import Interconnection

class TestInterconnectionTypes(unittest.TestCase):
    def setUp(self):
        self.cgra_dim = (4, 4)
        self.II = 2
        self.mapping = Mapping(num_vertices=1)
        self.node = 0
        self.mapping.placement = {
            0: (1, 1, 0)  # Nó no centro da malha
        }

    def test_mesh(self):
        inter = Interconnection(self.cgra_dim, "1000", self.mapping, self.II)
        neighbors = set(inter.neighbor_dict[self.node])
        expected = {
            (1, 1, 1),  # mesmo lugar
            (0, 1, 1),  # cima
            (2, 1, 1),  # baixo
            (1, 0, 1),  # esquerda
            (1, 2, 1)   # direita
        }
        self.assertEqual(neighbors, expected)

    def test_diagonal(self):
        inter = Interconnection(self.cgra_dim, "0100", self.mapping, self.II)
        neighbors = set(inter.neighbor_dict[self.node])
        expected = {
            (1, 1, 1),
            (0, 0, 1),  # cima-esquerda
            (0, 2, 1),  # cima-direita
            (2, 0, 1),  # baixo-esquerda
            (2, 2, 1)   # baixo-direita
        }
        self.assertEqual(neighbors, expected)

    def test_one_hop(self):
        inter = Interconnection(self.cgra_dim, "0010", self.mapping, self.II)
        neighbors = set(inter.neighbor_dict[self.node])
        expected = {
            (1, 1, 1),
            (1, 0, 1), (1, 2, 1), (1, 3, 1),  # mesma linha
            (0, 1, 1), (2, 1, 1), (3, 1, 1)   # mesma coluna
        }
        self.assertEqual(neighbors, expected)

    def test_toroidal(self):
        inter = Interconnection(self.cgra_dim, "0001", self.mapping, self.II)
        neighbors = set(inter.neighbor_dict[self.node])
        expected = {
            (1, 1, 1),
            (0, 1, 1),  # cima
            (2, 1, 1),  # baixo
            (1, 0, 1),  # esquerda
            (1, 2, 1)   # direita
        }
        self.assertEqual(neighbors, expected)

    def test_full_interconnection(self):
        inter = Interconnection(self.cgra_dim, "1111", self.mapping, self.II)
        neighbors = set(inter.neighbor_dict[self.node])
        
        expected = set()

        # mesh
        expected.update({
            (1, 1, 1),
            (0, 1, 1), (2, 1, 1), (1, 0, 1), (1, 2, 1)
        })

        # diagonal
        expected.update({
            (0, 0, 1), (0, 2, 1), (2, 0, 1), (2, 2, 1)
        })

        # one-hop
        expected.update({
            (0, 1, 1), (2, 1, 1), (3, 1, 1),
            (1, 0, 1), (1, 2, 1), (1, 3, 1)
        })

        # toroidal (mas todos já estão cobertos no centro, sem wrap)
        expected.add((1, 1, 1))

        self.assertEqual(neighbors, expected)

if __name__ == "__main__":
    unittest.main()
