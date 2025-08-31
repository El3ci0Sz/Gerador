from collections import deque, defaultdict
from src.utils.Mapping import Mapping
import networkx as nx
import random

"""
Temos 2 opções, deixar da maneira como esta agora e so mudar para que o metodo que pega o vizinho do no atual, seja agora get_interconnection

Ou fazer algo melhor, fazer um dicionario com os vizinhos de cada no, gerados apartir de interconnections e depois passar como parametro para a classe, quando routing requisitar vizinhos de um no, ela dara como parametro o no (chave do dicionario), e retornara o valor do dicionario que é uma lista com os vizinhos, gerados apartir das interconexões
"""
class Routing_CGRA:
    def __init__(self, mapping:Mapping, dfg_tam:int, alpha:float, alpha2:float, cgra_graph = nx.DiGraph) -> None:
        self.dfg_tam = dfg_tam
        self.alpha = alpha
        self.alpha2 = alpha2
        self.mapping = mapping
        self.cgra_graph = cgra_graph 

    def get_routing(self):

        """
        Realiza o roteamento do DFG no CGRA, gerando os caminhos de roteamento.

        Args:
            mapping (Mapping): Objeto contendo dados do mapeamento.
        """
        self.mapping.dfg_edges = defaultdict(list)
        self.mapping.routing = {}

        position_to_node = {pos: node for node, pos in self.mapping.placement.items()}
        visited = set()

        queue = deque([random.randint(0, self.dfg_tam - 1)])
        visited.add(queue[0])

        while queue:
            current_node = queue.popleft()
            
            neighbors = self.neighbors_dict[current_node]
            for neighbor_pos in neighbors:
                if neighbor_pos not in position_to_node:
                    continue

                neighbor_node = position_to_node[neighbor_pos]

                if neighbor_node == current_node:
                    continue

                if neighbor_node in self.mapping.dfg_edges[current_node] or current_node in self.mapping.dfg_edges[neighbor_node]:
                    continue

                if neighbor_node not in visited:
                    self.mapping.dfg_edges[current_node].append(neighbor_node)
                    queue.append(neighbor_node)
                    visited.add(neighbor_node)

                else:
                    if random.random() < self.alpha:
                        self.mapping.dfg_edges[current_node].append(neighbor_node)

                        if random.random() < self.alpha2 and self.mapping.dfg_edges[neighbor_node]:
                            target_to_remove = random.choice(list(self.mapping.dfg_edges[neighbor_node]))
                            self.mapping.dfg_edges[neighbor_node].remove(target_to_remove)

    @staticmethod  
    def get_routing_path(mapping):
        """
        Retorna o caminho de roteamento de um nó para outro.

        Args:
            mapping (Mapping): Objeto contendo o mapeamento.
        """
        def dfs(current, path, dst):
            if current == dst:
                return path
            for next_node in mapping.dfg_edges.get(current, []):
                if next_node not in path:
                    result = dfs(next_node, path + [next_node], dst)
                    if result:
                        return result
            return None

        for source, targets in mapping.dfg_edges.items():
            for target in targets:
                if (source, target) not in mapping.routing:
                    path = dfs(source, [source], target)
                    if path:
                        mapping.routing[(source, target)] = path
                    else:
                        raise ValueError(f"Roteamento falhou entre {source} e {target}.")

        

   
