from collections import deque, defaultdict
from src.utils.Mapping import Mapping # Mapping é necessário para placement
import random
import networkx as nx # Importar networkx para anotação de tipo, se não estiver já global

class Routing_CGRA:
    # --- CONSTRUTOR DA CLASSE ---
    def __init__(self, mapping: Mapping, dfg_tam: int, alpha: float, alpha2: float, physical_cgra_graph: nx.DiGraph) -> None:
        # Armazena o objeto 'mapping' que contém o placement (onde cada nó do DFG foi alocado no CGRA)
        # e onde as arestas e rotas do DFG serão armazenadas.
        self.mapping = mapping
        # Número total de nós no DFG.
        self.dfg_tam = dfg_tam
        # Probabilidade de criar conexões adicionais (arestas no DFG) com nós já visitados.
        self.alpha = alpha
        # Probabilidade de remover uma aresta existente de um vizinho ao criar uma conexão com 'alpha'.
        self.alpha2 = alpha2
        # O grafo NetworkX que representa TODAS as conexões físicas possíveis no CGRA.
        # Este grafo vem da classe Interconnection e descreve o hardware.
        self.physical_cgra_graph = physical_cgra_graph
        
        # Chama o método principal que vai gerar as arestas do DFG.
        self.get_routing()
        
    # --- MÉTODO PRINCIPAL PARA GERAR AS ARESTAS DO DFG ---
    def get_routing(self):
        """
        Realiza a geração de arestas do DFG no CGRA,
        baseado no placement dos nós do DFG e na conectividade física do CGRA.
        A lógica central é uma Busca em Largura (BFS) modificada para explorar
        vizinhanças no CGRA e conectar nós do DFG.
        """
        # Inicializa/limpa o dicionário que armazenará as arestas do DFG.
        # A chave é o nó de origem do DFG, e o valor é uma lista de nós de destino do DFG.
        self.mapping.dfg_edges = defaultdict(list)
        # Inicializa/limpa o dicionário que armazenará as rotas (caminhos de PEs no CGRA)
        # para cada aresta do DFG. Será preenchido por get_routing_path.
        self.mapping.routing = {}

        # Cria um dicionário reverso para mapear uma posição no CGRA (r,c,t) de volta para o ID do nó do DFG
        # que está alocado naquela posição. Isso otimiza a verificação se um PE vizinho está ocupado.
        position_to_node = {pos: node_id for node_id, pos in self.mapping.placement.items()}
        
        # Conjunto para rastrear os nós do DFG que já foram adicionados à fila da BFS
        # e, portanto, "processados" como origem de novas arestas.
        visited_dfg_nodes = set()
        
        # Se o DFG não tem nós, não há o que fazer.
        if self.dfg_tam == 0:
            return

        # Garante que há nós alocados antes de tentar escolher um nó inicial.
        if not self.mapping.placement:
             return
        
        # Escolhe um nó do DFG aleatório (que esteja alocado) para iniciar a busca em largura (BFS).
        initial_dfg_node = random.choice(list(self.mapping.placement.keys()))
        # Inicializa a fila (deque) da BFS com o nó inicial.
        queue = deque([initial_dfg_node])
        # Adiciona o nó inicial ao conjunto de visitados.
        visited_dfg_nodes.add(initial_dfg_node)

        # Loop principal da BFS: continua enquanto houver nós na fila para processar.
        while queue:
            # Remove o próximo nó do DFG da fila para ser o nó "fonte" atual.
            current_dfg_node_id = queue.popleft()
            
            # Verifica se o nó DFG atual realmente tem uma alocação no CGRA.
            # (Medida de segurança, deveria sempre ter se entrou na fila corretamente).
            if current_dfg_node_id not in self.mapping.placement:
                continue 
            
            # Obtém as coordenadas (r,c,t) do PE onde o nó DFG atual está alocado.
            current_pe_r, current_pe_c, current_pe_t = self.mapping.placement[current_dfg_node_id]
            # Cria uma tupla representando o nó no grafo físico do CGRA.
            current_cgra_node = (current_pe_r, current_pe_c, current_pe_t)

            # Verifica se o nó CGRA (onde o DFG nó está) existe no grafo físico.
            # (Outra medida de segurança).
            if not self.physical_cgra_graph.has_node(current_cgra_node):
                continue
                
            # CONSULTA AO GRAFO FÍSICO:
            # Pega todos os PEs (já com o tempo t+1) que são diretamente alcançáveis
            # a partir do PE onde o 'current_dfg_node_id' está alocado.
            # 'successors' retorna os vizinhos para onde 'current_cgra_node' pode enviar dados.
            potential_next_cgra_coords = list(self.physical_cgra_graph.successors(current_cgra_node))
            # Embaralha a lista de vizinhos para introduzir aleatoriedade na formação de arestas.
            random.shuffle(potential_next_cgra_coords)

            # Itera sobre cada PE vizinho fisicamente alcançável.
            for next_cgra_coord_with_time in potential_next_cgra_coords: # Ex: (nr, nc, nt_proximo)
                # Verifica se este PE vizinho está ocupado por algum outro nó do DFG.
                if next_cgra_coord_with_time not in position_to_node:
                    # Se não estiver ocupado, não podemos formar uma aresta do DFG para ele. Pula.
                    continue

                # Se o PE vizinho está ocupado, pega o ID do nó do DFG que está lá.
                neighbor_dfg_node_id = position_to_node[next_cgra_coord_with_time]

                # Impede a criação de uma aresta de um nó DFG para ele mesmo nesta lógica.
                # (O grafo físico já trata de auto-loops de PEs para manter dados).
                if neighbor_dfg_node_id == current_dfg_node_id:
                    continue

                # Verifica se já existe uma aresta entre esses dois nós DFG (em qualquer direção)
                # para evitar adicionar arestas duplicadas ou ciclos imediatos durante a BFS.
                if neighbor_dfg_node_id in self.mapping.dfg_edges.get(current_dfg_node_id, []) or \
                   current_dfg_node_id in self.mapping.dfg_edges.get(neighbor_dfg_node_id, []):
                    continue

                # Se o nó DFG vizinho ainda não foi "visitado" (processado como origem na BFS):
                if neighbor_dfg_node_id not in visited_dfg_nodes:
                    # Cria a aresta no DFG do nó atual para o nó vizinho.
                    self.mapping.dfg_edges[current_dfg_node_id].append(neighbor_dfg_node_id)
                    # Adiciona o nó DFG vizinho à fila da BFS para ser processado depois.
                    queue.append(neighbor_dfg_node_id)
                    # Marca o nó DFG vizinho como visitado.
                    visited_dfg_nodes.add(neighbor_dfg_node_id)
                else:
                    # Se o nó DFG vizinho JÁ FOI VISITADO, aplica a lógica probabilística:
                    # Com probabilidade 'alpha', cria uma aresta adicional.
                    if random.random() < self.alpha:
                        self.mapping.dfg_edges[current_dfg_node_id].append(neighbor_dfg_node_id)
                        
                        # Se a aresta com 'alpha' foi criada, então com probabilidade 'alpha2',
                        # remove uma aresta aleatória que SAÍA do 'neighbor_dfg_node_id'.
                        if random.random() < self.alpha2 and self.mapping.dfg_edges.get(neighbor_dfg_node_id):
                            targets_of_neighbor = self.mapping.dfg_edges[neighbor_dfg_node_id]
                            if targets_of_neighbor: # Se há arestas saindo do vizinho
                                target_to_remove = random.choice(targets_of_neighbor)
                                self.mapping.dfg_edges[neighbor_dfg_node_id].remove(target_to_remove)
                                # Se essa aresta removida tinha uma rota definida, remove a rota também.
                                if (neighbor_dfg_node_id, target_to_remove) in self.mapping.routing:
                                    del self.mapping.routing[(neighbor_dfg_node_id, target_to_remove)]

     # --- MÉTODO PARA DEFINIR OS CAMINHOS DE ROTEAMENTO NO CGRA PARA AS ARESTAS DO DFG ---
    def get_routing_path(self):
        """
        Preenche self.mapping.routing com os caminhos de PEs no CGRA.
        A DFS interna aqui serve para confirmar a alcançabilidade dentro do grafo DFG gerado.
        Para arestas diretas A->B no DFG, o caminho no CGRA será [PE_de_A, PE_de_B].
        """
        
        # Função auxiliar recursiva para a Busca em Profundidade (DFS).
        # Esta DFS opera sobre o GRAFO DFG (self.mapping.dfg_edges) para encontrar
        # um caminho de NÓS DO DFG entre 'current_dfg_node' e 'target_dfg_node'.
        def dfs(current_dfg_node, path_nodes, target_dfg_node):
            # Caso base: se o nó DFG atual é o nó DFG de destino, retorna o caminho de nós DFG acumulado.
            if current_dfg_node == target_dfg_node:
                return path_nodes
            
            # Para cada nó DFG vizinho (conectado por uma aresta do DFG)
            for next_dfg_node in self.mapping.dfg_edges.get(current_dfg_node, []):
                # Se o próximo nó DFG ainda não está no caminho atual (evita ciclos na DFS)
                if next_dfg_node not in path_nodes:
                    # Chamada recursiva
                    result_path_nodes = dfs(next_dfg_node, path_nodes + [next_dfg_node], target_dfg_node)
                    # Se a chamada recursiva encontrou um caminho, propaga o resultado.
                    if result_path_nodes:
                        return result_path_nodes
            # Se nenhum caminho foi encontrado a partir deste ponto.
            return None

        # Itera sobre todas as arestas do DFG que foram geradas em 'get_routing'.
        for source_dfg_node, target_dfg_nodes_list in self.mapping.dfg_edges.items():
            for target_dfg_node in target_dfg_nodes_list:
                # Se uma rota para esta aresta do DFG ainda não foi calculada:
                if (source_dfg_node, target_dfg_node) not in self.mapping.routing:
                    # A DFS aqui, no contexto de arestas já criadas por get_routing,
                    # essencialmente confirma que target_dfg_node é alcançável a partir de source_dfg_node
                    # no grafo DFG. Para uma aresta direta (S,D), path_of_dfg_nodes será [S,D].
                    path_of_dfg_nodes = dfs(source_dfg_node, [source_dfg_node], target_dfg_node)
                    
                    if path_of_dfg_nodes:
                        # Converte o caminho de nós do DFG para um caminho de PEs do CGRA (r,c,t).
                        # Cada nó no 'path_of_dfg_nodes' é um ID de nó DFG.
                        # Buscamos sua alocação em 'self.mapping.placement'.
                        path_of_cgra_pes = [self.mapping.placement[node_id] for node_id in path_of_dfg_nodes]
                        # Armazena o caminho de PEs do CGRA para a aresta do DFG.
                        self.mapping.routing[(source_dfg_node, target_dfg_node)] = path_of_cgra_pes
                    else:
                        # Este 'else' normalmente não deveria ser atingido se a aresta (source_dfg_node, target_dfg_node)
                        # realmente existe em self.mapping.dfg_edges, pois a DFS deveria encontrar o caminho direto [source, target].
                        # Se for uma aresta simples (não multi-hop no DFG), o caminho é direto.
                        if target_dfg_node in self.mapping.dfg_edges.get(source_dfg_node, []):
                             # Para uma conexão direta, o caminho de PEs são os PEs de origem e destino.
                             path_of_cgra_pes = [self.mapping.placement[source_dfg_node], self.mapping.placement[target_dfg_node]]
                             self.mapping.routing[(source_dfg_node, target_dfg_node)] = path_of_cgra_pes
