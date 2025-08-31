import networkx as nx

class QCA:
    """
    Fábrica de Grafos de Conectividade para Arquiteturas QCA.
    Gera um grafo base que representa todas as conexões direcionais
    possíveis para uma dada arquitetura física.
    """
    def __init__(self, qca_dim, arch_type) -> None:
        self.dim = qca_dim
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

    def get_graph(self):
        """Método público principal para obter o grafo de conectividade gerado."""
        return self._generate_connectivity_graph()

    def _generate_connectivity_graph(self):
        graph = nx.DiGraph()
        all_nodes = self._get_all_nodes()

        for node in all_nodes:
            neighbors = set()
            
            if self.arch_type == "U":
                neighbors.update(self._get_neighbors_by_clock_flow(node, self._get_use_clock_zone))
            elif self.arch_type == "T":
                neighbors.update(self._get_neighbors_2DDWave(node))
            elif self.arch_type == "R": 
                neighbors.update(self._get_neighbors_by_clock_flow(node, self._get_res_clock_zone))
            else:
                raise ValueError(f"Tipo de arquitetura desconhecido: {self.arch_type}")

            self._build_edges(node, neighbors, graph)

        return graph

    def _build_edges(self, node, neighbors, graph:nx.DiGraph):
        """Adiciona as arestas de SAÍDA do nó para seus vizinhos."""
        for neighbor in neighbors:
            graph.add_edge(node, neighbor)
 
    def _get_all_nodes(self) -> list:
        return [(row, col) for row in range(self.dim[0]) for col in range(self.dim[1])]

    def _is_valid_node(self, node):
        r, c = node
        return 0 <= r < self.dim[0] and 0 <= c < self.dim[1]
    
    def _get_use_clock_zone(self, node):
        r, c = node
        return self.USE_CLOCK_TILE[r % 4][c % 4]

    def _get_res_clock_zone(self, node): 
        """Calcula a zona de clock (1-4) para um nó na arquitetura RES."""
        r, c = node
        return self.RES_CLOCK_TILE[r % 4][c % 4]
    
    
    def _get_neighbors_by_clock_flow(self, node, clock_zone_func): 
        """
        Lógica genérica para encontrar vizinhos em esquemas de clock direcionais (USE, RES).
        Recebe como argumento a função que determina a zona de clock.
        """
        r, c = node
        source_zone = clock_zone_func(node)
        target_zone = (source_zone % 4) + 1
        
        potential_neighbors = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
        
        valid_neighbors = set()
        for neighbor in potential_neighbors:
            if self._is_valid_node(neighbor):
                neighbor_zone = clock_zone_func(neighbor)
                if neighbor_zone == target_zone:
                    valid_neighbors.add(neighbor)
                    
        return valid_neighbors

    def _get_neighbors_2DDWave(self, node):
        r, c = node
        potential_neighbors = [
            (r, c + 1),  # Vizinho a Leste
            (r + 1, c)   # Vizinho ao Sul
        ]
        return {n for n in potential_neighbors if self._is_valid_node(n)}

    def get_border_nodes(self):
        """ Retorna um conjunto de todas as coordenadas na borda da grade. """
        rows, cols = self.dim
        borders = set()
        for r in range(rows):
            for c in range(cols):
                if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                    borders.add((r, c))
        return borders
