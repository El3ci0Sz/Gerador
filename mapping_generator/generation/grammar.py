# mapping_generator/generation/grammar.py

import random
import networkx as nx
import logging

logger = logging.getLogger(__name__)

class Grammar:
    """Implements the grammar-based procedural generation of a DFG on an architecture graph."""

    def __init__(self, architecture_graph: nx.DiGraph, border_nodes: set, grid_dim: tuple, 
                 target_size: int, recipe: dict, k_range: tuple, max_path_length: int, 
                 no_extend_io: bool):
        """Initializes the Grammar engine."""
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
    
    def generate(self, growth_timeout: int = 200) -> nx.DiGraph | None:
        """Main method to generate a graph according to the specified parameters."""
        if not list(self.arch_graph.nodes()): return None
        available_nodes = list(set(self.arch_graph.nodes()) - self.used_nodes)
        if not available_nodes: return None
        
        start_node = random.choice(available_nodes)
        self.placement_graph.add_node(start_node)
        self.used_nodes.add(start_node)
        logger.debug(f"Grammar generation started. Initial node: {start_node}")

        steps = 0
        while len(self.used_nodes) < self.target_size and steps < growth_timeout:
            if not self._apply_pattern():
                break
            steps += 1
        
        logger.debug(f"Growth phase finished. Nodes generated: {len(self.used_nodes)}/{self.target_size}")
        
        recipe_fulfilled = (self.reconvergences_created >= self.recipe.get('reconvergence', 0) and
                            self.convergences_created >= self.recipe.get('convergence', 0))
        
        # --- CORREÇÃO CRÍTICA AQUI ---
        # A condição agora é '==' para garantir o tamanho exato do grafo.
        if len(self.used_nodes) == self.target_size and recipe_fulfilled:
            return self.placement_graph
        else:
            if not recipe_fulfilled:
                logger.debug("Mandatory recipe not fulfilled. Discarding graph.")
            elif len(self.used_nodes) != self.target_size:
                 logger.debug(f"Final graph size ({len(self.used_nodes)}) does not match target size ({self.target_size}). Discarding graph.")
            return None

    def _apply_pattern(self) -> bool:
        """Applies a single grammar rule to grow the graph."""
        self.step_counter += 1
        budget = self.target_size - len(self.used_nodes)
        if budget <= 0: return False

        logger.debug(f"Step {self.step_counter}: Budget={budget}, CurrentNodes={len(self.used_nodes)}")
        
        recipe_fulfilled = (self.reconvergences_created >= self.recipe.get('reconvergence', 0) and
                            self.convergences_created >= self.recipe.get('convergence', 0))

        if not recipe_fulfilled:
            potential_rules = []
            if self.reconvergences_created < self.recipe.get('reconvergence', 0):
                potential_rules.append(self._reconvergence_rule)
            if self.convergences_created < self.recipe.get('convergence', 0):
                potential_rules.append(self._convergence_rule)
            
            random.shuffle(potential_rules)
            for rule in potential_rules:
                if rule(budget):
                    return True

        logger.debug("Phase 2 / Fallback: Attempting tree rule.")
        if self._tree_rule(budget):
            return True
        
        logger.warning("No rule could be applied. Growth has stalled.")
        return False
    
    def _tree_rule(self, budget: int) -> bool:
        """Tries to add simple tree-like branches from multiple existing nodes."""
        if not self.used_nodes or budget < 1: return False
        
        potential_start_nodes = list(self.used_nodes)
        random.shuffle(potential_start_nodes)
        max_start_node_attempts = 5 
        
        for start_node in potential_start_nodes[:max_start_node_attempts]:
            k_max_by_budget = budget 
            k_max_allowed = min(self.k_range[1], k_max_by_budget)
            if k_max_allowed < 1: continue
            k = random.randint(1, k_max_allowed)
            
            free_nodes = list(set(self.arch_graph.nodes()) - self.used_nodes - {start_node})
            random.shuffle(free_nodes)
            
            paths = []
            newly_claimed_in_this_call = set()
            for target_node in free_nodes:
                if len(paths) >= k: break
                path = self._find_shortest_path(start_node, target_node, newly_claimed_in_this_call)
                if path:
                    new_nodes_from_path = set(path) - self.used_nodes
                    if len(newly_claimed_in_this_call.union(new_nodes_from_path)) <= budget:
                        paths.append(path)
                        newly_claimed_in_this_call.update(new_nodes_from_path)
            
            if paths:
                self._add_paths_to_placement(paths, f"Tree (k={len(paths)})")
                return True

        logger.debug("Tree rule failed: could not find valid branches from multiple start nodes.")
        return False

    def _convergence_rule(self, budget: int) -> bool:
        """Tries to create a convergence pattern towards an existing node."""
        min_cost = self.k_range[0]
        if not self.used_nodes or budget < min_cost: return False
        target_node = random.choice(list(self.used_nodes))
        k_max_allowed = min(self.k_range[1], budget)
        if k_max_allowed < self.k_range[0]: return False
        k = random.randint(self.k_range[0], k_max_allowed)
        source_pool = list(set(self.arch_graph.nodes()) - self.used_nodes - {target_node})
        random.shuffle(source_pool)

        paths = []
        newly_claimed_in_this_call = set()
        for source_node in source_pool:
            if len(paths) >= k: break
            path = self._find_shortest_path(source_node, target_node, newly_claimed_in_this_call)
            if path:
                new_nodes_from_path = set(path) - self.used_nodes
                if len(newly_claimed_in_this_call.union(new_nodes_from_path)) <= budget:
                    paths.append(path)
                    newly_claimed_in_this_call.update(new_nodes_from_path)

        if len(paths) >= self.k_range[0]:
            self._add_paths_to_placement(paths, f"Convergence (k={len(paths)})")
            self.convergences_created += 1
            return True
        return False

    # ... (O resto dos métodos permanecem os mesmos) ...
    def _reconvergence_rule(self, budget: int) -> bool:
        min_cost = self.k_range[0] + 1
        if not self.used_nodes or budget < min_cost: return False
        k_max_allowed = min(self.k_range[1], budget - 1)
        if k_max_allowed < self.k_range[0]: return False
        k = random.randint(self.k_range[0], k_max_allowed)
        start_node = random.choice(list(self.used_nodes))
        target_pool = list(set(self.arch_graph.nodes()) - self.used_nodes - {start_node})
        random.shuffle(target_pool)
        for target_node in target_pool:
            paths_found = self._find_disjoint_paths(start_node, target_node, k, budget)
            if paths_found:
                self._add_paths_to_placement(paths_found, f"Reconvergence (k={len(paths_found)})")
                self.reconvergences_created += 1
                return True
        return False
        
    def _find_shortest_path(self, source, target, extra_nodes_to_avoid=None) -> list | None:
        try:
            nodes_to_avoid = self.used_nodes.copy()
            if extra_nodes_to_avoid:
                nodes_to_avoid.update(extra_nodes_to_avoid)
            nodes_to_avoid -= {source, target}
            subgraph = self.arch_graph.copy()
            subgraph.remove_nodes_from(nodes_to_avoid)
            path = nx.shortest_path(subgraph, source=source, target=target)
            return path if path and (len(path) - 1 <= self.max_path_length) else None
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def _find_disjoint_paths(self, source, target, k, budget) -> list | None:
        try:
            subgraph = self.arch_graph.copy()
            subgraph.remove_nodes_from(self.used_nodes - {source, target})
            paths = list(nx.all_shortest_paths(subgraph, source, target))
            if len(paths) >= k:
                return random.sample(paths, k)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
        return None

    def _add_paths_to_placement(self, paths: list, rule_name: str):
        if not paths: return
        logger.debug(f"Commit: Rule '{rule_name}' adding {len(paths)} path(s).")
        for path in paths:
            self.used_nodes.update(path)
            nx.add_path(self.placement_graph, path)
