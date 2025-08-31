import os
import random
from math import ceil
import json
import networkx as nx
import logging

from src.mapping_utils.mapping_generator_CGRA import Mapping_generator_CGRA
from src.mapping_utils.mapping_generator_CGRA_Grammar import Mapping_generator_CGRA_Grammar
from src.mapping_utils.mapping_generator_QCA_Grammar import Mapping_generator_QCA
from src.cgra.CGRA_UTIL import CGRA_UTIL
from src.utils.Graph_Visualizer import Graph_Visualizer

logger = logging.getLogger(__name__)

class MappingControler:
    def __init__(self, gen_mode, tec, k, difficulty, tam_arch, cgra_params, graph_range, recipe, k_range, no_extend_io, max_path_length, no_images, qca_arch):
        self.gen_mode = gen_mode
        self.tec = tec
        self.k = k
        self.difficulty = difficulty
        self.tam_arch = tam_arch
        self.cgra_params = cgra_params
        self.graph_range = graph_range
        self.recipe = recipe
        self.k_range = k_range
        self.no_extend_io = no_extend_io
        self.max_path_length = max_path_length
        self.no_images = no_images
        self.qca_arch = qca_arch
        
    def run(self):
        if self.tec == '0': # CGRA
            logger.info("Tecnologia Alvo: CGRA")
            if self.gen_mode == 'grammar':
                return self._run_cgra_grammar_generation()
            elif self.gen_mode == 'random':
                return self._run_cgra_random_generation()
        
        elif self.tec == '1': # QCA
            logger.info("Tecnologia Alvo: QCA")
            if self.gen_mode == 'grammar':
                return self._run_qca_grammar_generation()
            else:
                logger.error("Modo 'random' não é suportado para QCA.")
                return False
        return False

    def _run_cgra_random_generation(self):
        logger.info(f"Iniciando geração de {self.k} mapeamentos aleatórios para CGRA...")
        saved_graph_count = 0
        for i in range(self.k):
            try:
                num_vertices = random.randint(self.graph_range[0], self.graph_range[1])
                grid_size = random.choice(self.tam_arch)
                row, col = grid_size
                II = ceil(num_vertices / (row * col)) if (row*col) > 0 else float('inf')

                mapping_generator = Mapping_generator_CGRA(
                    dfg_tam=num_vertices, 
                    II=II, 
                    alpha=0.8,
                    alpha2=0.4,
                    cgra_dim=grid_size, 
                    bits=self.cgra_params['bits']
                )
                mapping_obj = mapping_generator.mapp()
                
                final_graph = nx.DiGraph()
                node_map = {}
                for node_id, pos in mapping_obj.placement.items():
                    final_graph.add_node(tuple(pos), name=node_id, opcode='add')
                    node_map[node_id] = tuple(pos)

                for (src_id, dst_id), path in mapping_obj.routing.items():
                    if src_id in node_map and dst_id in node_map:
                        src_node = node_map[src_id]
                        dst_node = node_map[dst_id]
                        if not final_graph.has_edge(src_node, dst_node):
                            final_graph.add_edge(src_node, dst_node)
                
                saved_graph_count += 1
                logger.info(f"Grafo aleatório Válido {saved_graph_count}/{self.k} gerado. Salvando...")
                self.save_all_files(
                    final_graph, "CGRA", "mappings_cgra_random", 
                    grid_size, saved_graph_count, cgra_bits=self.cgra_params['bits']
                )

            except Exception as e:
                logger.error(f"ERRO ao gerar mapa CGRA aleatório: {e}", exc_info=True)
        return saved_graph_count == self.k

    def _run_qca_grammar_generation(self):
        logger.info(f"Iniciando geração de {self.k} grafos via gramática para QCA...")
        saved_graph_count = 0
        for i in range(self.k):
            try:
                grid_size = random.choice(self.tam_arch)
                grammar_steps = random.randint(self.graph_range[0], self.graph_range[1])

                qca_gen = Mapping_generator_QCA(
                    grid_dim=grid_size,
                    qca_arch_type=self.qca_arch,
                    grammar_steps=grammar_steps,
                    k_range=self.k_range,
                    no_extend_io=self.no_extend_io,
                    max_path_length=self.max_path_length,
                    balance_paths=True
                )
                final_graph = qca_gen.mapp(min_nodes=self.graph_range[0])
                
                if final_graph:
                    for i_node, node_coord in enumerate(list(final_graph.nodes())):
                         final_graph.nodes[node_coord]['name'] = f'op{i_node}'

                    saved_graph_count += 1
                    logger.info(f"Grafo QCA Válido {saved_graph_count}/{self.k} gerado. Salvando...")
                    self.save_all_files(final_graph, "QCA", "mappings_qca_grammar", grid_size, saved_graph_count)

            except Exception as e:
                logger.error(f"ERRO CRÍTICO na geração QCA: {e}", exc_info=True)
        return saved_graph_count == self.k

    def _run_cgra_grammar_generation(self):
        saved_graph_count = 0; total_attempts = 0
        max_total_attempts = self.k * 150
        logger.info(f"Iniciando geração de {self.k} grafos para dificuldade {self.difficulty} com receita: '{self.recipe}'")
        while saved_graph_count < self.k and total_attempts < max_total_attempts:
            total_attempts += 1
            try:
                target_nodes = random.randint(self.graph_range[0], self.graph_range[1])
                grid_size = random.choice(self.tam_arch)
                row, col = grid_size; II = int(ceil(target_nodes / (row * col)) if (row * col) > 0 else float('inf'))
                cgra_grammar_gen = Mapping_generator_CGRA_Grammar(
                    cgra_dim=grid_size, II=II, bits=self.cgra_params['bits'], 
                    num_nodes=target_nodes, recipe=self.recipe, k_range=self.k_range,
                    no_extend_io=self.no_extend_io, max_path_length=self.max_path_length
                )
                final_graph = cgra_grammar_gen.mapp()
                if not final_graph: continue
                saved_graph_count += 1
                logger.info(f"Grafo CGRA Válido {saved_graph_count}/{self.k} gerado. Salvando...")
                for i_node, node_coord in enumerate(list(final_graph.nodes())):
                    final_graph.nodes[node_coord]['name'] = f'add{i_node}'; final_graph.nodes[node_coord]['opcode'] = 'add'
                self.save_all_files(
                    final_graph, "CGRA", "mappings_cgra_grammar", 
                    grid_size, saved_graph_count, cgra_bits=self.cgra_params['bits']
                )
            except Exception as e:
                logger.error(f"ERRO CRÍTICO na geração CGRA: {e}", exc_info=True)
                continue
        return saved_graph_count >= self.k

    def save_all_files(self, graph, tec_name, base_folder, grid_size, index, **kwargs):
        row, col = grid_size; num_nodes = graph.number_of_nodes(); arch_str = f"{row}x{col}"
        if tec_name == "CGRA":
            bits = kwargs.get('cgra_bits', '0000')
            BIT_POSITION_TO_NAME = {0: "mesh", 1: "diagonal", 2: "one-hop", 3: "toroidal"}
            if bits == "1111": interconnect_name = "all"
            else: interconnect_name = "-".join(filter(None, [BIT_POSITION_TO_NAME.get(i) for i, bit in enumerate(bits) if bit == '1']))
            if not interconnect_name: interconnect_name = "custom_config"
            directory = f"{base_folder}/{interconnect_name}/{arch_str}/{num_nodes}_nodes"
        else: # Para QCA
            directory = f"{base_folder}/{self.qca_arch}/{arch_str}/{num_nodes}_nodes"
        
        os.makedirs(directory, exist_ok=True)
        filename_base = f"{tec_name.lower()}_map_diff{self.difficulty}_{arch_str}_N{num_nodes}_E{graph.number_of_edges()}_{index}"
        path_base = f"{directory}/{filename_base}"
        mii_required = max(1, int(ceil(num_nodes / (row * col)) if (row * col) > 0 else float('inf')))
        if not self.no_images:
            Graph_Visualizer.generate_custom_dot_and_image(graph, f"{path_base}.dot", path_base)
        self._save_mapping_as_json(
            graph=graph, path_base=path_base, tec=tec_name, arch_dim=grid_size,
            mii=mii_required, interconnect_name=kwargs.get('interconnect_name'), **kwargs
        )

    def _save_mapping_as_json(self, graph, path_base, tec, arch_dim, mii=None, **kwargs):
        json_data = {'graph_name': os.path.basename(path_base),'graph_properties': {'node_count': graph.number_of_nodes(), 'edge_count': graph.number_of_edges(),'II': mii},'generation_properties': {'difficulty': self.difficulty,'recipe': self.recipe},'architecture_properties': {'type': tec,'dimensions': list(arch_dim),'interconnection_name': kwargs.get('interconnect_name', 'unknown')},'placement': {graph.nodes[node].get('name', 'unknown_name'): list(node) for node in graph.nodes()},'edges': [[graph.nodes[u].get('name', 'unknown_name'), graph.nodes[v].get('name', 'unknown_name')] for u, v in graph.edges()]}
        json_filename = f"{path_base}.json"
        try:
            import re
            pretty_json_string = json.dumps(json_data, indent=4)
            compacted_json_string = re.sub(r'\[\s+(\d+),\s+(\d+),\s+(\d+)\s+\]', r'[\1, \2, \3]', pretty_json_string)
            with open(json_filename, 'w') as f: f.write(compacted_json_string)
            logger.info(f"Arquivo JSON salvo em '{json_filename}'")
        except Exception as e:
            logger.error(f"ERRO ao salvar o arquivo JSON: {e}")
