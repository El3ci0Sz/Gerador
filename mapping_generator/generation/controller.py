# mapping_generator/generation/controller.py

import os
import random
import json
import logging
from math import ceil
import networkx as nx

from ..architectures.cgra import CgraArch
from ..architectures.qca import QCA
from ..utils.visualizer import GraphVisualizer
from .grammar import Grammar
from .random_cgra_generator import RandomCgraGenerator
from ..architectures.cgra import CgraArch as CGRAInterconnection

logger = logging.getLogger(__name__)

def generate_recipes(max_difficulty: int) -> dict:
    """Dynamically generates a dictionary of recipes for increasing complexity.

    Args:
        max_difficulty (int): The maximum difficulty level to generate recipes for.

    Returns:
        dict: A dictionary where keys are difficulty levels and values are recipe dicts.
    """
    recipes = {1: {"reconvergence": 0, "convergence": 0}}
    if max_difficulty == 1:
        return recipes
    r, c = 0, 0
    for i in range(2, max_difficulty + 1):
        if r == c: c += 1
        elif c > r: r, c = c, r
        elif r > c + 1: c += 1
        else: r, c = c, r + 1
        recipes[i] = {"reconvergence": r, "convergence": c}
    return recipes

class GenerationTask:
    """Manages the execution of a single generation task for a specific configuration."""
    def __init__(self, tec, gen_mode, k, difficulty, arch_sizes, cgra_params, graph_range, 
                 recipe, k_range, no_extend_io, max_path_length, no_images, qca_arch, 
                 ii=None, output_dir='results', alpha=0.3, retries_multiplier=150):
        """Initializes the Generation Task with all necessary parameters."""
        self.tec = tec
        self.gen_mode = gen_mode
        self.k = k
        self.difficulty = difficulty
        self.arch_sizes = arch_sizes
        self.cgra_params = cgra_params
        self.graph_range = graph_range
        self.recipe = recipe
        self.k_range = k_range
        self.no_extend_io = no_extend_io
        self.max_path_length = max_path_length
        self.no_images = no_images
        self.qca_arch = qca_arch
        self.fixed_ii = ii
        self.output_dir = output_dir
        self.alpha = alpha
        self.retries_multiplier = retries_multiplier

    def run(self) -> bool:
        """Runs the generation task based on the initialized parameters.

        Returns:
            bool: True if the required number of graphs were generated, False otherwise.
        """
        if self.tec == 'cgra':
            if self.gen_mode == 'grammar':
                return self._run_cgra_grammar()
            elif self.gen_mode == 'random':
                return self._run_cgra_random()
        elif self.tec == 'qca':
            if self.gen_mode == 'grammar':
                return self._run_qca_grammar()
            else:
                logger.error(f"Generation mode '{self.gen_mode}' is not supported for QCA.")
                return False
        return False

    def _run_cgra_grammar(self) -> bool:
        """Executes the grammar-based generation for CGRA."""
        saved_graph_count = 0
        total_attempts = 0
        consecutive_failures = 0
        max_total_attempts = self.k * 150
        max_consecutive_failures = self.k * 10 

        logger.info(f"Starting CGRA grammar task: k={self.k}, difficulty={self.difficulty}, recipe={self.recipe}")

        while saved_graph_count < self.k:
            if total_attempts >= max_total_attempts or consecutive_failures >= max_consecutive_failures:
                level = "warning" if consecutive_failures >= max_consecutive_failures else "error"
                getattr(logger, level)(
                    f"Stopping task due to excessive failures. Total: {total_attempts}, Consecutive: {consecutive_failures}"
                )
                break
            
            total_attempts += 1
            try:
                target_nodes = random.randint(self.graph_range[0], self.graph_range[1])
                arch_size = random.choice(self.arch_sizes)
                rows, cols = arch_size
                II = int(ceil(target_nodes / (rows * cols))) if (rows * cols) > 0 else 1

                interconnection = CGRAInterconnection(arch_size, self.cgra_params['bits'], II)
                
                grammar = Grammar(
                    architecture_graph=interconnection.get_graph(),
                    border_nodes=interconnection.get_border_nodes(),
                    grid_dim=arch_size,
                    target_size=target_nodes,
                    recipe=self.recipe,
                    k_range=self.k_range,
                    max_path_length=self.max_path_length,
                    no_extend_io=self.no_extend_io
                )
                final_graph = grammar.generate()

                if not final_graph:
                    consecutive_failures += 1
                    continue

                consecutive_failures = 0
                saved_graph_count += 1
                logger.info(f"Valid CGRA grammar graph {saved_graph_count}/{self.k} generated. Saving...")
                self._prepare_and_save(final_graph, "CGRA", "mappings_cgra_grammar", arch_size, saved_graph_count, bits=self.cgra_params['bits'])
            except Exception as e:
                logger.error(f"Critical error during CGRA grammar generation: {e}", exc_info=True)
                consecutive_failures += 1
                continue
        
        return saved_graph_count >= self.k

    def _run_cgra_random(self) -> bool:
        """Executes random DFG generation for CGRA, now using the constructive logic."""
        logger.info(f"Starting random CGRA task: k={self.k}, graph_range={self.graph_range}")
        saved_graph_count = 0
        for i in range(self.k):
            try:
                num_nodes = random.randint(self.graph_range[0], self.graph_range[1])
                arch_size = random.choice(self.arch_sizes)
                row,col = arch_size
                
                II = ceil(num_nodes/(row * col))

                generator = RandomCgraGenerator(dfg_size=num_nodes, II=II, cgra_dim=arch_size, bits=self.cgra_params['bits'])
                mapping_obj = generator.generate_mapping()
                
                if not mapping_obj:
                    logger.warning("Random generator failed to produce a valid mapping.")
                    continue
                
                final_graph = nx.DiGraph()
                node_map = {}
                for node_id, pos in mapping_obj.placement.items():
                    final_graph.add_node(tuple(pos))
                    node_map[node_id] = tuple(pos)
                for (src_id, dst_id) in mapping_obj.routing.keys():
                    if src_id in node_map and dst_id in node_map:
                        final_graph.add_edge(node_map[src_id], node_map[dst_id])
                
                saved_graph_count += 1
                logger.info(f"Valid random CGRA graph {saved_graph_count}/{self.k} generated. Saving...")
                
                self._prepare_and_save(final_graph, "CGRA", "mappings_cgra_random", arch_size, saved_graph_count, name_prefix='add', bits=self.cgra_params['bits'])
            
            except Exception as e:
                logger.error(f"Error generating random CGRA map: {e}", exc_info=True)
        return saved_graph_count == self.k

    def _run_qca_grammar(self) -> bool:
        """Executes grammar-based generation for QCA with a robust retry loop."""

        logger.info(f"Starting QCA grammar task: k={self.k}, arch_type={self.qca_arch}")
        saved_graph_count = 0
        total_attempts = 0
        max_total_attempts = self.k * self.retries_multiplier

        while saved_graph_count < self.k and total_attempts < max_total_attempts:
            total_attempts += 1
            try:
                arch_size = random.choice(self.arch_sizes)
                target_nodes = random.randint(self.graph_range[0], self.graph_range[1])
                qca_arch = QCA(arch_size, self.qca_arch)
                
                grammar = Grammar(
                    architecture_graph=qca_arch.get_graph(),
                    border_nodes=qca_arch.get_border_nodes(),
                    grid_dim=arch_size,
                    target_size=target_nodes,
                    recipe={"reconvergence": 0, "convergence": 0},
                    k_range=self.k_range,
                    max_path_length=self.max_path_length,
                    no_extend_io=self.no_extend_io
                )
                final_graph = grammar.generate()
                
                if final_graph:
                    saved_graph_count += 1
                    logger.info(f"Valid QCA grammar graph {saved_graph_count}/{self.k} generated. Saving...")
                    self._prepare_and_save(final_graph, "QCA", "op", arch_size, saved_graph_count)

            except Exception as e:
                logger.error(f"Critical error during QCA grammar generation: {e}", exc_info=True)
        
        if saved_graph_count < self.k:
            logger.warning(f"QCA task finished but only generated {saved_graph_count}/{self.k} graphs.")
            
        return saved_graph_count >= self.k   

    def _prepare_and_save(self, graph, tec_name, base_folder, arch_size, index, name_prefix: str = 'op', **kwargs):
        """Assigns logical names with a specific prefix to nodes and triggers the save process."""
        for i, node_coord in enumerate(list(graph.nodes())):
            graph.nodes[node_coord]['name'] = f'{name_prefix}_{i}'
            graph.nodes[node_coord]['opcode'] = name_prefix
        
        self._save_all_files(graph, tec_name, base_folder, arch_size, index, **kwargs)

    def _save_all_files(self, graph, tec_name, base_folder, arch_size, index, **kwargs):
        """Saves all output files (.dot, .json, .png) for a generated graph."""
        rows, cols = arch_size
        num_nodes = graph.number_of_nodes()
        arch_str = f"{rows}x{cols}"
        
        interconnect_name = "default"
        if tec_name == "CGRA":
            bits = kwargs.get('bits', '0000')
            BIT_TO_NAME = {0: "mesh", 1: "diagonal", 2: "one_hop", 3: "toroidal"}
            if bits == "1111": interconnect_name = "all"
            else: interconnect_name = "-".join(filter(None, [BIT_TO_NAME.get(i) for i, b in enumerate(bits) if b == '1']))
            if not interconnect_name: interconnect_name = "custom"
            output_dir = os.path.join(base_folder, interconnect_name, arch_str, f"{num_nodes}_nodes")
        else: # For QCA
            output_dir = os.path.join(base_folder, self.qca_arch, arch_str, f"{num_nodes}_nodes")
        
        os.makedirs(output_dir, exist_ok=True)
        
        filename_base = f"{tec_name.lower()}_map_diff{self.difficulty}_{arch_str}_N{num_nodes}_E{graph.number_of_edges()}_{index}"
        path_base = os.path.join(output_dir, filename_base)
        
        if not self.no_images:
            GraphVisualizer.generate_custom_dot_and_image(graph, f"{path_base}.dot", path_base)
        
        self._save_mapping_as_json(graph, path_base, tec_name, arch_size, **kwargs)

    def _save_mapping_as_json(self, graph, path_base, tec_name, arch_size, **kwargs):
        """Saves the mapping data to a JSON file, conditionally adding fields."""
        rows, cols = arch_size
        num_nodes = graph.number_of_nodes()
        mii = int(ceil(num_nodes / (rows * cols))) if (rows * cols) > 0 else 1

        properties = {'node_count': num_nodes, 'edge_count': graph.number_of_edges(), 'II_required': mii}
        # CORREÇÃO: Apenas adiciona difficulty e recipe se o modo for 'grammar'
        if self.gen_mode == 'grammar':
            properties['difficulty'] = self.difficulty
            properties['recipe'] = self.recipe

        json_data = {
            'graph_name': os.path.basename(path_base),
            'properties': properties,
            'architecture': {'technology': tec_name, 'dimensions': list(arch_size)},
            'placement': {graph.nodes[node].get('name'): list(node) for node in graph.nodes()},
            'edges': [(graph.nodes[u].get('name'), graph.nodes[v].get('name')) for u, v in graph.edges()]
        }
        if tec_name == "CGRA":
            json_data['architecture']['interconnect_bits'] = kwargs.get('bits')

        json_filename = f"{path_base}.json"
        try:
            with open(json_filename, 'w') as f:
                json.dump(json_data, f, indent=4)
            logger.info(f"JSON file saved to '{json_filename}'")
        except Exception as e:
            logger.error(f"Error saving JSON file: {e}")

