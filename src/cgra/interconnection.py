from src.utils.Mapping import Mapping
import networkx as nx
"""
Para verificar e mudar, terminar de fazer as interconexões, e nao esquecer de verificar se para cada no, nao a vizinhos iguais entre as interconexões, por exemplo pegar um vizinho mesh que seja o mesmo diagonal, verificação para ignorar se for igual

Verificar tambem o que pode ser geral e o que pode ser modulado para tornar o codigo melhor.
"""

class Interconnection:
    def __init__(self, cgra_dim,interconnection:str, II) -> None:
        self.bits = Interconnection.get_bits(interconnection)
        self.cgra_dim = cgra_dim
        self.II = II

    """
        bits:
        1000,1 bit = mesh
        0100,2 bit = diagonal
        0010,3 bit = one-hop
        0001,4 bit = toroidal
    """
    def get_interconnections(self):
        graph = nx.DiGraph()
        row , col = self.cgra_dim

        for r in range(row):
            for c in range(col):
                for t in range(self.II):
                    neighbors = set()
                    node = (r,c)

                    if self.bits[0] == 1:
                        neighbors.update(self.mesh(node))
                    if self.bits[1] == 1:
                        neighbors.update(self.diagonal(node))
                    if self.bits[2] == 1:
                        neighbors.update(self.one_hop(node))
                    if self.bits[3] == 1:
                        neighbors.update(self.toroidal(node))

                    self.build_edges(node, neighbors,t, graph)

        return graph

    def get_border_nodes(self):
        """NOVO: Retorna um conjunto de todos os nós que estão na borda física do CGRA."""
        rows, cols = self.cgra_dim
        borders = set()
        for t in range(self.II):
            for r in range(rows):
                for c in range(cols):
                    if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                        borders.add((r, c,t))
        return borders

    def build_edges(self, node, neighbors, t,graph:nx.DiGraph):

        r,c = node
        next_t = (t + 1) % self.II

        for neighbor in neighbors:

            nr , nc = neighbor
            graph.add_edge((r,c,t), (nr,nc,next_t))
    
        if self.II > 1:
            graph.add_edge((r,c,t), (r,c,next_t))

    def get_graph(self):
        return self.get_interconnections()

    def get_neighbors(self, pe_coord , directions, toroidal=False):

        rows, cols = self.cgra_dim
        r,c = pe_coord 
        neighbors = set()

        if toroidal:
            # Toroidal horizontal (coluna)
            if c == 0:
                neighbors.add((r, cols - 1)) 
            elif c == cols - 1:
                neighbors.add((r, 0))

            # Toroidal vertical (linha)
            if r == 0:
                neighbors.add((rows - 1, c))  
            elif r == rows - 1:
                neighbors.add((0, c))         

        else:
            for x, y in directions:
                next_row, next_col = r + x, c + y

                if 0 <= next_row < rows and 0 <= next_col < cols:
                    neighbors.add((next_row, next_col))

        return neighbors

    def mesh(self,node):

        directions = [
            (-1, 0),   # cima
            (1, 0),    # baixo
            (0, -1),   # esquerda
            (0, 1)     # direita
        ]

        return self.get_neighbors(node, directions)

    def diagonal(self, node):

        directions = [
            (-1, -1),   # diagonal: cima esquerda
            (-1, 1),    # diagonal: cima direita
            (1, -1),   # diagonal: baixo esquerda
            (1, 1)     # diagonal: baixo direita
        ]

        return self.get_neighbors(node, directions)
    
    def one_hop(self, node):

        directions = [
            (-2, 0),   # cima 
            (2, 0),    # baixo 
            (0, -2),   # esquerda 
            (0, 2)     # direita 
        ]
        return self.get_neighbors(node,directions)
        
    def toroidal(self, node):

                return self.get_neighbors(node,directions=[],toroidal=True)
    
    @staticmethod
    def get_bits(interconnection):
        interconnection = interconnection.ljust(4,'0')
        bits = [int(x) for x in interconnection]
        return bits
