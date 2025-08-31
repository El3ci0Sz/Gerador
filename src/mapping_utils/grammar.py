import random
import networkx as nx
import logging

logger = logging.getLogger(__name__)

class Grammar:
    # ... (todo o resto da classe permanece igual, exceto a função generate) ...
    def __init__(self, architecture_graph: nx.DiGraph, border_nodes: set, grid_dim: tuple, target_size: int, recipe: dict, k_range: tuple, max_path_length: int, no_extend_io: bool):
        self.arch_graph = architecture_graph
        self.border_nodes = border_nodes
        self.grid_dim = grid_dim
        self.target_size = target_size
        self.recipe = recipe
        self.k_range = k_range
        self.max_path_length = max_path_length
        self.no_extend_io = no_extend_io
        self.placement_graph = nx.DiGraph()
        self.used_nodes = set()
        self.step_counter = 0
        self.reconvergences_created = 0
        self.convergences_created = 0

    def _find_shortest_path(self, source, target, nodes_to_avoid_extra=None):
        try:
            nodes_to_avoid = self.used_nodes.copy()
            if nodes_to_avoid_extra:
                nodes_to_avoid.update(nodes_to_avoid_extra)
            nodes_to_avoid -= {source, target}
            if target in nodes_to_avoid or source in nodes_to_avoid: return None
            subgraph = self.arch_graph.copy()
            subgraph.remove_nodes_from(nodes_to_avoid)
            path = nx.shortest_path(subgraph, source=source, target=target)
            return path if path and (len(path) - 1 <= self.max_path_length) else None
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def _add_paths_to_placement(self, paths: list, rule_name: str):
        if not paths: return
        logger.debug(f"    [COMMIT] Regra '{rule_name}' a adicionar {len(paths)} caminho(s):")
        for path in paths:
            logger.debug(f"      - Caminho: {path}")
            self.used_nodes.update(path)
            nx.add_path(self.placement_graph, path)

    def arvore(self, budget):
        if not self.used_nodes or budget < 1: return False
        start_node = random.choice(list(self.used_nodes))
        logger.debug(f"    [ARVORE] A tentar criar a partir de {start_node}")
        k_max_by_budget = budget 
        k_max_allowed = min(self.k_range[1], k_max_by_budget, 4)
        if k_max_allowed < 1: return False
        k = random.randint(1, k_max_allowed)
        logger.debug(f"    [ARVORE] Budget permite k max de {k_max_allowed}. Sorteado k={k}")
        free_nodes = list(set(self.arch_graph.nodes()) - self.used_nodes - {start_node})
        random.shuffle(free_nodes)
        paths, temp_claimed_nodes = [], set()
        for target_node in free_nodes:
            if len(paths) >= k: break
            if target_node in temp_claimed_nodes: continue
            path = self._find_shortest_path(start_node, target_node, temp_claimed_nodes)
            if path:
                new_nodes = set(path) - self.used_nodes
                if len(temp_claimed_nodes) + len(new_nodes) <= budget:
                    paths.append(path)
                    temp_claimed_nodes.update(path)
        if paths:
            self._add_paths_to_placement(paths, f"Árvore (k={len(paths)})")
            return True
        logger.debug("    [ARVORE] Falhou: não encontrou ramos válidos.")
        return False

    def convergence(self, budget):
        min_cost = self.k_range[0]
        if not self.used_nodes or budget < min_cost: return False
        target_node = random.choice(list(self.used_nodes))
        logger.debug(f"    [CONVERGENCIA] A tentar criar para o alvo EXISTENTE {target_node}")
        k_max_by_budget = budget
        k_max_allowed = min(self.k_range[1], k_max_by_budget, 4)
        if k_max_allowed < self.k_range[0]: return False
        k = random.randint(self.k_range[0], k_max_allowed)
        logger.debug(f"    [CONVERGENCIA] Budget permite k max de {k_max_allowed}. Sorteado k={k}")
        source_pool = list(set(self.arch_graph.nodes()) - self.used_nodes - {target_node})
        random.shuffle(source_pool)
        paths, temp_claimed_nodes = [], set()
        for source_node in source_pool:
            if len(paths) >= k: break
            if source_node in temp_claimed_nodes: continue
            path = self._find_shortest_path(source_node, target_node, temp_claimed_nodes)
            if path:
                new_nodes = set(path) - self.used_nodes
                if len(temp_claimed_nodes) + len(new_nodes) <= budget:
                    paths.append(path)
                    temp_claimed_nodes.update(path)
        if len(paths) >= self.k_range[0]:
            self._add_paths_to_placement(paths, f"Convergência (k={len(paths)})")
            self.convergences_created += 1
            return True
        logger.debug("    [CONVERGENCIA] Falhou: não encontrou caminhos suficientes.")
        return False

    def reconvergence(self, budget):
        min_cost = self.k_range[0] + 1
        if budget < min_cost: return False
        k_max_by_budget = budget - 1
        k_max_allowed = min(self.k_range[1], k_max_by_budget, 4)
        if k_max_allowed < self.k_range[0]: return False
        k = random.randint(self.k_range[0], k_max_allowed)
        logger.debug(f"    [RECONVERGENCIA] Budget permite k max de {k_max_allowed}. Sorteado k={k}")
        if random.choice(['entrada', 'saida']) == 'saida':
            if not self.used_nodes: return False
            start_node = random.choice(list(self.used_nodes))
            target_pool = list(set(self.arch_graph.nodes()) - self.used_nodes - {start_node})
            random.shuffle(target_pool)
            for target_node in target_pool:
                paths_found = self._find_balanced_paths(start_node, target_node, k, budget)
                if paths_found:
                    self._add_paths_to_placement(paths_found, "Reconvergência de Saída")
                    self.reconvergences_created += 1
                    return True
        else:
            if not self.used_nodes: return False
            target_node = random.choice(list(self.used_nodes))
            source_pool = list(set(self.arch_graph.nodes()) - self.used_nodes - {target_node})
            if len(source_pool) < k: return False
            paths_found = self._find_balanced_paths_multi_source(source_pool, target_node, k, budget)
            if paths_found:
                self._add_paths_to_placement(paths_found, "Reconvergência de Entrada")
                self.reconvergences_created += 1
                return True
        logger.debug("    [RECONVERGENCIA] Falhou.")
        return False
    
    def _find_balanced_paths(self, start_node, target_node, k, budget):
        logger.debug(f"    [RECONV-HELPER] A tentar {start_node} -> {target_node} com k={k}")
        try:
            subgraph = self.arch_graph.copy()
            subgraph.remove_nodes_from(self.used_nodes - {start_node, target_node})
            candidate_paths = list(nx.all_shortest_paths(subgraph, source=start_node, target=target_node))
            if not candidate_paths or len(candidate_paths[0]) -1 > self.max_path_length: return None
            if len(candidate_paths) < k: return None
            random.shuffle(candidate_paths)
            selected_paths = []
            claimed_intermediate_nodes = set()
            for path in candidate_paths:
                if len(selected_paths) >= k: break
                intermediate_nodes = set(path[1:-1])
                if claimed_intermediate_nodes.isdisjoint(intermediate_nodes):
                    current_cost = len((claimed_intermediate_nodes | intermediate_nodes | {start_node, target_node}) - self.used_nodes)
                    if current_cost <= budget:
                        selected_paths.append(path)
                        claimed_intermediate_nodes.update(intermediate_nodes)
            if len(selected_paths) == k:
                return selected_paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
        return None

    def _find_balanced_paths_multi_source(self, source_pool, target_node, k, budget):
        logger.debug(f"    [RECONV-HELPER] A tentar k={k} fontes -> {target_node}")
        subgraph = self.arch_graph.copy()
        subgraph.remove_nodes_from(self.used_nodes - set(source_pool) - {target_node})
        candidate_paths, target_len = [], -1
        for source in source_pool:
            try:
                paths = list(nx.all_shortest_paths(subgraph, source=source, target=target_node))
                if paths:
                    if target_len == -1:
                        if len(paths[0]) -1 <= self.max_path_length:
                            target_len = len(paths[0])
                            candidate_paths.extend(paths)
                    elif len(paths[0]) == target_len:
                        candidate_paths.extend(paths)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
        if len(candidate_paths) < k: return None
        random.shuffle(candidate_paths)
        selected_paths, claimed_nodes = [], {target_node}
        for path in candidate_paths:
            if len(selected_paths) >= k: break
            path_nodes = set(path)
            if claimed_nodes.isdisjoint(path_nodes):
                current_cost = len((claimed_nodes | path_nodes) - self.used_nodes)
                if current_cost <= budget:
                    selected_paths.append(path)
                    claimed_nodes.update(path_nodes)
        if len(selected_paths) == k:
            return selected_paths
        return None

    def generate_pattern(self):
        self.step_counter += 1
        budget = self.target_size - len(self.used_nodes)
        if budget <= 0: return False
        logger.debug(f"\n--- PASSO {self.step_counter} --- Orçamento: {budget}, Nós Atuais: {len(self.used_nodes)} ---")
        logger.debug(f"    Receita: {self.recipe} | Criadas: R={self.reconvergences_created}, C={self.convergences_created}")
        recipe_fulfilled = (self.reconvergences_created >= self.recipe.get('reconvergence', 0) and
                            self.convergences_created >= self.recipe.get('convergence', 0))
        if not recipe_fulfilled:
            potential_rules = []
            if self.reconvergences_created < self.recipe.get('reconvergence', 0):
                potential_rules.append(self.reconvergence)
            if self.convergences_created < self.recipe.get('convergence', 0):
                potential_rules.append(self.convergence)
            random.shuffle(potential_rules)
            for rule in potential_rules:
                logger.debug(f"  [FASE 1] Tentando regra da receita: {rule.__name__}")
                if rule(budget):
                    return True
        logger.debug("  [FASE 2 / FALLBACK] Preenchendo com ÁRVORE...")
        if self.arvore(budget):
            return True
        logger.debug("  AVISO: Nenhuma regra pôde ser aplicada. Crescimento travado.")
        return False

    def generate(self, growth_timeout=2000):
        if not list(self.arch_graph.nodes()): return None
        available_nodes = list(set(self.arch_graph.nodes()) - self.used_nodes)
        if not available_nodes: return None
        start_node = random.choice(available_nodes)
        self.placement_graph.add_node(start_node)
        self.used_nodes.add(start_node)
        logger.debug(f"--- INÍCIO DA GERAÇÃO --- Nó inicial: {start_node}")
        steps = 0
        while len(self.used_nodes) < self.target_size and steps < growth_timeout:
            if not self.generate_pattern():
                break
            steps += 1
        
        # MUDANÇA: Log rebaixado de INFO para DEBUG
        logger.debug(f"--- FIM DO CRESCIMENTO --- Nós gerados: {len(self.used_nodes)}/{self.target_size}")
        
        recipe_fulfilled = (self.reconvergences_created >= self.recipe.get('reconvergence', 0) and
                            self.convergences_created >= self.recipe.get('convergence', 0))
        
        if len(self.used_nodes) >= self.target_size and recipe_fulfilled:
            return self.placement_graph
        else:
            if not recipe_fulfilled:
                logger.warning(f"Receita OBRIGATÓRIA não cumprida. Descartando grafo.")
            return None

    def merge(self, alpha=0.15):
        """ Adiciona arestas extras entre nós vizinhos já mapeados para aumentar a conectividade. """
        logger.debug("  [PÓS-PROCESSAMENTO] Executando MERGE...")
        possible_edges = list(self.arch_graph.edges())
        random.shuffle(possible_edges)
        edges_added = 0
        for u, v in possible_edges:
            if u in self.used_nodes and v in self.used_nodes:
                if not self.placement_graph.has_edge(u, v):
                    # Garante que não criará um ciclo
                    if not nx.has_path(self.placement_graph, v, u):
                        if random.random() < alpha:
                            self.placement_graph.add_edge(u, v)
                            edges_added += 1
        logger.debug(f"    - Arestas adicionadas no merge: {edges_added}")

    def synchronize_io_and_extend_to_border(self):
        """ Estende os nós de entrada e saída até a borda física da arquitetura. """
        logger.debug("  [PÓS-PROCESSAMENTO] Executando EXTENSÃO DE I/O...")
        if not self.placement_graph.nodes: return

        # Calcula os níveis para identificar I/Os
        try:
            for node in nx.topological_sort(self.placement_graph):
                level = 0
                preds = list(self.placement_graph.predecessors(node))
                if preds:
                    level = max(self.placement_graph.nodes[p].get('level', -1) for p in preds) + 1
                self.placement_graph.nodes[node]['level'] = level
        except nx.NetworkXUnfeasible:
            logger.warning("Grafo contém ciclos, impossível estender I/O.")
            return

        io_nodes = [n for n in self.placement_graph.nodes if self.placement_graph.in_degree(n) == 0 or self.placement_graph.out_degree(n) == 0]
        
        for node in io_nodes:
            # Lógica para estender até a borda (simplificada para o exemplo)
            # A sua implementação original pode ser mais complexa
            if node in self.border_nodes: continue
            
            closest_border_node = min(self.border_nodes, key=lambda bn: abs(bn[0]-node[0]) + abs(bn[1]-node[1]))
            
            path_to_border = self._find_shortest_path(node, closest_border_node)
            if path_to_border:
                logger.debug(f"    - Estendendo nó {node} para a borda via {path_to_border}")
                self._add_paths_to_placement([path_to_border], "Extend I/O")
