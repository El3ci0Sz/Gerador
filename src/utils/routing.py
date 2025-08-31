from collections import deque, defaultdict
from src.utils.Mapping import Mapping 
import random
import networkx as nx

class Routing:
    def __init__(self, mapping: Mapping, dfg_tam: int, alpha: float, alpha2: float, physical_graph: nx.DiGraph) -> None:
        self.mapping = mapping
        self.dfg_tam = dfg_tam
        self.alpha = alpha
        self.alpha2 = alpha2
        self.physical_graph = physical_graph
        self.get_routing() 
        
    def get_routing(self):
        """
        Realiza o roteamento (geração de arestas do DFG) no CGRA, 
        baseado no placement e na conectividade física do CGRA.
        """
        self.mapping.dfg_edges = defaultdict(list)
        self.mapping.routing = {}

        position_to_node = {pos: node_id for node_id, pos in self.mapping.placement.items()}
        
        visited_dfg_nodes = set()
        
        if self.dfg_tam == 0:
            return

        if not self.mapping.placement: 
             return
        
        initial_dfg_node = random.choice(list(self.mapping.placement.keys()))
        queue = deque([initial_dfg_node])
        visited_dfg_nodes.add(initial_dfg_node)

        while queue:
            current_dfg_node_id = queue.popleft()
            
            if current_dfg_node_id not in self.mapping.placement:
                continue 
            
            current_pe_r, current_pe_c, current_pe_t = self.mapping.placement[current_dfg_node_id]
            current_cgra_node = (current_pe_r, current_pe_c, current_pe_t)

            if not self.physical_graph.has_node(current_cgra_node):
                print(f"Alerta: Nó CGRA {current_cgra_node} do DFG {current_dfg_node_id} não encontrado no grafo físico.")
                continue
                
            potential_next_cgra_coords = list(self.physical_graph.successors(current_cgra_node))
            random.shuffle(potential_next_cgra_coords) 

            for next_cgra_coord_with_time in potential_next_cgra_coords:
                if next_cgra_coord_with_time not in position_to_node:
                    continue 

                neighbor_dfg_node_id = position_to_node[next_cgra_coord_with_time]

                if neighbor_dfg_node_id == current_dfg_node_id:
                    continue

                if neighbor_dfg_node_id in self.mapping.dfg_edges.get(current_dfg_node_id, []) or \
                   current_dfg_node_id in self.mapping.dfg_edges.get(neighbor_dfg_node_id, []):
                    continue

                if neighbor_dfg_node_id not in visited_dfg_nodes:
                    self.mapping.dfg_edges[current_dfg_node_id].append(neighbor_dfg_node_id)
                    queue.append(neighbor_dfg_node_id)
                    visited_dfg_nodes.add(neighbor_dfg_node_id)
                else:
                    if random.random() < self.alpha:
                        self.mapping.dfg_edges[current_dfg_node_id].append(neighbor_dfg_node_id)

                        if random.random() < self.alpha2 and self.mapping.dfg_edges.get(neighbor_dfg_node_id):
                            targets_of_neighbor = self.mapping.dfg_edges[neighbor_dfg_node_id]
                            
                            if targets_of_neighbor:
                                target_to_remove = random.choice(targets_of_neighbor)
                                self.mapping.dfg_edges[neighbor_dfg_node_id].remove(target_to_remove)
                                if (neighbor_dfg_node_id, target_to_remove) in self.mapping.routing:
                                    del self.mapping.routing[(neighbor_dfg_node_id, target_to_remove)]

    def get_routing_path(self):
        """
        Preenche self.mapping.routing com os caminhos encontrados no DFG.
        Este método assume que as arestas em self.mapping.dfg_edges são
        as arestas lógicas do DFG que precisam ser "realizadas" ou documentadas.
        Se a "rota" é apenas a conexão direta entre PEs (como implícito pela
        geração de arestas em get_routing), então o "path" será apenas [source_pe, target_pe].
        A DFS atual encontra caminhos no grafo DFG, não no grafo CGRA.
        """

        def dfs(current_dfg_node, path_nodes, target_dfg_node):
            if current_dfg_node == target_dfg_node:
                return path_nodes

            for next_dfg_node in self.mapping.dfg_edges.get(current_dfg_node, []):
                if next_dfg_node not in path_nodes:
                    result_path_nodes = dfs(next_dfg_node, path_nodes + [next_dfg_node], target_dfg_node)
                    if result_path_nodes:
                        return result_path_nodes
            return None

        for source_dfg_node, target_dfg_nodes_list in self.mapping.dfg_edges.items():
            for target_dfg_node in target_dfg_nodes_list:
                if (source_dfg_node, target_dfg_node) not in self.mapping.routing:
                    path_of_dfg_nodes = dfs(source_dfg_node, [source_dfg_node], target_dfg_node)

                    if path_of_dfg_nodes:
                        path_of_cgra_pes = [self.mapping.placement[node_id] for node_id in path_of_dfg_nodes]
                        self.mapping.routing[(source_dfg_node, target_dfg_node)] = path_of_cgra_pes
                    else:
                        if target_dfg_node in self.mapping.dfg_edges.get(source_dfg_node, []):
                             path_of_cgra_pes = [self.mapping.placement[source_dfg_node], self.mapping.placement[target_dfg_node]]
                             self.mapping.routing[(source_dfg_node, target_dfg_node)] = path_of_cgra_pes


