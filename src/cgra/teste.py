while(True):
    t = int(input("t > "))
    II = int(input("II > "))
    print((1 + t) % II)

from collections import deque, defaultdict
from src.utils.Mapping import Mapping # Mapping é necessário para placement
import random
import networkx as nx # Importar networkx se ainda não estiver

class Routing_CGRA:
    def __init__(self, mapping: Mapping, dfg_tam: int, alpha: float, alpha2: float, physical_cgra_graph: nx.DiGraph) -> None:
        self.mapping = mapping # Armazena o objeto mapping
        self.dfg_tam = dfg_tam
        self.alpha = alpha
        self.alpha2 = alpha2
        self.physical_cgra_graph = physical_cgra_graph # Armazena o grafo físico
        
        self.get_routing() # Chama o método de roteamento na inicialização
        
    def get_routing(self):
        """
        Realiza o roteamento (geração de arestas do DFG) no CGRA, 
        baseado no placement e na conectividade física do CGRA.
        """
        self.mapping.dfg_edges = defaultdict(list)
        # self.mapping.routing foi movido para ser preenchido em get_routing_path
        # Se precisar inicializar aqui por algum motivo:
        self.mapping.routing = {}


        # Dicionário reverso para facilitar a busca: Posição no CGRA -> nó do DFG
        position_to_node = {pos: node_id for node_id, pos in self.mapping.placement.items()}
        
        visited_dfg_nodes = set()
        
        if self.dfg_tam == 0: # Se não há nós no DFG, não há o que rotear
            return

        # Iniciar a busca a partir de um nó aleatório do DFG
        # Garante que o nó inicial exista no placement
        if not self.mapping.placement: # Se placement estiver vazio
             return
        
        initial_dfg_node = random.choice(list(self.mapping.placement.keys()))
        queue = deque([initial_dfg_node])
        visited_dfg_nodes.add(initial_dfg_node)

        while queue:
            current_dfg_node_id = queue.popleft()
            
            # Obter a posição (r,c,t) do nó DFG atual no CGRA
            if current_dfg_node_id not in self.mapping.placement:
                continue # Nó DFG não está alocado, pular
            
            current_pe_r, current_pe_c, current_pe_t = self.mapping.placement[current_dfg_node_id]
            current_cgra_node = (current_pe_r, current_pe_c, current_pe_t)

            # --- ALTERADO: Usar o physical_cgra_graph para obter vizinhos ---
            # Os sucessores já são tuplas (nr, nc, nt) onde nt = (t_atual + 1) % II
            if not self.physical_cgra_graph.has_node(current_cgra_node):
                # Isso não deveria acontecer se o placement só usa PEs válidos
                # e o physical_cgra_graph cobre todos os PEs válidos.
                # print(f"Alerta: Nó CGRA {current_cgra_node} do DFG {current_dfg_node_id} não encontrado no grafo físico.")
                continue
                
            potential_next_cgra_coords = list(self.physical_cgra_graph.successors(current_cgra_node))
            random.shuffle(potential_next_cgra_coords) # Para variar as conexões

            for next_cgra_coord_with_time in potential_next_cgra_coords: # ex: (nr, nc, nt_proximo)
                # Verifica se a coordenada vizinha no CGRA está ocupada por outro nó do DFG
                if next_cgra_coord_with_time not in position_to_node:
                    continue # Posição vizinha no CGRA está livre ou não é um destino válido

                neighbor_dfg_node_id = position_to_node[next_cgra_coord_with_time]

                if neighbor_dfg_node_id == current_dfg_node_id:
                    # O grafo físico já lida com self-loops (PE para si mesmo no tempo t+1)
                    # Aqui estamos tratando de arestas entre diferentes nós do DFG.
                    continue

                # Evitar arestas duplicadas ou na direção oposta nesta etapa da BFS
                if neighbor_dfg_node_id in self.mapping.dfg_edges.get(current_dfg_node_id, []) or \
                   current_dfg_node_id in self.mapping.dfg_edges.get(neighbor_dfg_node_id, []):
                    continue

                if neighbor_dfg_node_id not in visited_dfg_nodes:
                    self.mapping.dfg_edges[current_dfg_node_id].append(neighbor_dfg_node_id)
                    queue.append(neighbor_dfg_node_id)
                    visited_dfg_nodes.add(neighbor_dfg_node_id)
                else:
                    # Lógica de conexão probabilística com alpha
                    if random.random() < self.alpha:
                        self.mapping.dfg_edges[current_dfg_node_id].append(neighbor_dfg_node_id)
                        # Lógica de remoção probabilística com alpha2
                        if random.random() < self.alpha2 and self.mapping.dfg_edges.get(neighbor_dfg_node_id):
                            # Pega a lista de destinos do neighbor_dfg_node_id
                            targets_of_neighbor = self.mapping.dfg_edges[neighbor_dfg_node_id]
                            if targets_of_neighbor: # Verifica se a lista não está vazia
                                target_to_remove = random.choice(targets_of_neighbor)
                                self.mapping.dfg_edges[neighbor_dfg_node_id].remove(target_to_remove)
                                # Também remover de self.mapping.routing se já existir
                                if (neighbor_dfg_node_id, target_to_remove) in self.mapping.routing:
                                    del self.mapping.routing[(neighbor_dfg_node_id, target_to_remove)]


    # --- ALTERADO: Tornando get_routing_path um método de instância ---
    def get_routing_path(self):
        """
        Preenche self.mapping.routing com os caminhos encontrados no DFG.
        Este método assume que as arestas em self.mapping.dfg_edges são
        as arestas lógicas do DFG que precisam ser "realizadas" ou documentadas.
        Se a "rota" é apenas a conexão direta entre PEs (como implícito pela
        geração de arestas em get_routing), então o "path" será apenas [source_pe, target_pe].
        A DFS atual encontra caminhos no grafo DFG, não no grafo CGRA.
        """
        
        # Limpa rotas anteriores para o caso de re-roteamento ou múltiplas chamadas
        # self.mapping.routing = {} # Movido para __init__ ou início de get_routing

        def dfs(current_dfg_node, path_nodes, target_dfg_node):
            if current_dfg_node == target_dfg_node:
                return path_nodes
            
            for next_dfg_node in self.mapping.dfg_edges.get(current_dfg_node, []):
                if next_dfg_node not in path_nodes: # Evitar ciclos no caminho DFS atual
                    # O caminho para o DFS deve ser de nós do DFG
                    result_path_nodes = dfs(next_dfg_node, path_nodes + [next_dfg_node], target_dfg_node)
                    if result_path_nodes:
                        return result_path_nodes
            return None

        for source_dfg_node, target_dfg_nodes_list in self.mapping.dfg_edges.items():
            for target_dfg_node in target_dfg_nodes_list:
                # A chave da rota é (source_dfg_node, target_dfg_node)
                if (source_dfg_node, target_dfg_node) not in self.mapping.routing:
                    # Encontra caminho de nós DFG
                    path_of_dfg_nodes = dfs(source_dfg_node, [source_dfg_node], target_dfg_node)
                    
                    if path_of_dfg_nodes:
                        # O que armazenar em self.mapping.routing?
                        # Opção 1: O caminho de nós do DFG (como está)
                        # self.mapping.routing[(source_dfg_node, target_dfg_node)] = path_of_dfg_nodes

                        # Opção 2: O caminho de PEs (r,c,t) no CGRA correspondente a esses nós DFG
                        path_of_cgra_pes = [self.mapping.placement[node_id] for node_id in path_of_dfg_nodes]
                        self.mapping.routing[(source_dfg_node, target_dfg_node)] = path_of_cgra_pes
                    else:
                        # Se a DFS não encontra um caminho no grafo DFG gerado, isso indica um problema
                        # na lógica de get_routing ou que a aresta não deveria existir.
                        # Ou a DFS não é o que se espera aqui.
                        # Para arestas diretas do DFG (A->B), o caminho é apenas [A, B].
                        # Se A->B é uma aresta, dfs(A, [A], B) retornará [A,B]
                        # print(f"Alerta: Não foi possível encontrar caminho DFS no DFG de {source_dfg_node} para {target_dfg_node}, embora a aresta exista.")
                        # Se uma aresta (S,D) existe em dfg_edges, o caminho mais simples é [S,D]
                        # A DFS aqui é para garantir que D é alcançável a partir de S no grafo DFG.
                        # Se for apenas para registrar a conexão direta:
                        if target_dfg_node in self.mapping.dfg_edges.get(source_dfg_node, []):
                             path_of_cgra_pes = [self.mapping.placement[source_dfg_node], self.mapping.placement[target_dfg_node]]
                             self.mapping.routing[(source_dfg_node, target_dfg_node)] = path_of_cgra_pes
                        # else:
                        #     raise ValueError(f"Roteamento falhou entre DFG {source_dfg_node} e DFG {target_dfg_node} via DFS.")
