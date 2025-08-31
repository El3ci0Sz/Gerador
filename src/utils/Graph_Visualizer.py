
import os
import json
import matplotlib.pyplot as plt
import networkx as nx
from src.utils.Mapping import Mapping
from collections import defaultdict

class Graph_Visualizer:
    
    @staticmethod
    def generate_image_from_dot(dot_file):
        """
        Gera uma imagem do grafo a partir de um arquivo DOT e salva no mesmo diretório.

        Args:
            dot_file (str): Caminho para o arquivo DOT.
        """
        directory = os.path.dirname(dot_file)
        output_file = os.path.join(directory, os.path.splitext(os.path.basename(dot_file))[0] + ".png")

        os.system(f"dot -Tpng {dot_file} -o {output_file}")

    @staticmethod
    def plot_cgra(mapping, cgra_dim, routing=True, output_file="cgra.png"):
        """
        Gera uma representação gráfica do CGRA com subplots para cada ciclo de II.
        """
        # (Este método permanece inalterado)
        rows, cols = cgra_dim
        II = max(pos[2] for pos in mapping.placement.values()) + 1
        fig, axes = plt.subplots(nrows=1, ncols=II, figsize=(5 * II, 5))

        if II == 1:
            axes = [axes]

        for cycle in range(II):
            ax = axes[cycle]
            ax.set_xlim(-0.5, cols - 0.5)
            ax.set_ylim(-0.5, rows - 0.5)
            ax.set_xticks(range(cols))
            ax.set_yticks(range(rows))
            ax.grid(True, linestyle='--', linewidth=0.5)
            ax.set_aspect('equal')
            ax.invert_yaxis()

            for node, (x, y, z) in mapping.placement.items():
                if z == cycle:
                    ax.text(y, x, f"{node}\n({x},{y},{z})", ha='center', va='center', fontsize=8, color='blue')

            ax.set_title(f"Cycle {cycle}")
            ax.set_xlabel("Coluna (y)")
            ax.set_ylabel("Linha (x)")

        plt.tight_layout()
        plt.savefig(output_file)
        print(f"Imagem salva em {output_file}")
        plt.close(fig)

    @staticmethod
    def export_to_dot(mapping, filename):
        # (Este método permanece inalterado)
        with open(filename, "w", encoding="utf-8") as f:
            f.write("strict digraph {\n")

            for node in sorted(mapping.placement.keys()):
                f.write(f'    {node} [opcode=add];\n')

            for (src, dst) in sorted(mapping.routing.keys()):
                f.write(f'    {src} -> {dst};\n')

            f.write("}\n")

    @staticmethod
    def export_to_json(mapping:Mapping, graph_name:str, path:str):
        # (Este método permanece inalterado)
        routing_serializable = {str(key): value for key, value in mapping.routing.items()}
        mapping_to_json = {
            "graph_name" : graph_name,
            "node_to_pe" :  mapping.placement,
            "routing" : routing_serializable 
        }
        json_name = f"{path}.json"
        try:
            with open(json_name, 'w') as j:
                json.dump(mapping_to_json, j , indent=4)
            print(f"Salvo com sucesso em {json_name}")
        except IOError as e:
            print(f"Erro ao salvar o arquivo: {e}")
        except TypeError as e:
            print(f"Erro ao serializar para JSON: {e}")     

    @staticmethod
    def generate_custom_dot_and_image(graph: nx.DiGraph, dot_filename: str, output_image_filename: str):
        """
        CORRIGIDO: Gera um arquivo .dot usando os atributos 'name' existentes no grafo.
        """
        if not graph or not graph.nodes:
            print("[GraphVisualizer] Grafo vazio, nenhuma imagem para gerar.")
            return

        levels = defaultdict(list)
        try:
            for node in nx.topological_sort(graph):
                level = 0
                for pred in graph.predecessors(node):
                    level = max(level, graph.nodes[pred].get('level', -1) + 1)
                graph.nodes[node]['level'] = level
                levels[level].append(node)
        except nx.NetworkXUnfeasible:
            print("AVISO: Grafo possui ciclos, não foi possível calcular os níveis para o alinhamento.")
            levels.clear()

        try:
            with open(dot_filename, "w", encoding="utf-8") as f:
                f.write("strict digraph {\n")
                f.write("    rankdir=TB;\n")

                # Escreve a definição dos nós
                for node, data in graph.nodes(data=True):
                    node_name = data.get('name', str(node))
                    opcode = data.get('opcode', 'op')
                    # --- LINHA CORRIGIDA ---
                    # Removemos o atributo 'name' de dentro dos colchetes.
                    f.write(f'    "{node_name}" [opcode={opcode}];\n')

                f.write("\n")

                # Escreve as arestas
                for src, dst in sorted(graph.edges()):
                    source_name = graph.nodes[src].get('name', str(src))
                    dest_name = graph.nodes[dst].get('name', str(dst))
                    f.write(f'    "{source_name}" -> "{dest_name}";\n')
                
                if levels:
                    for level in sorted(levels.keys()):
                        nodes_in_level = " ".join([f'"{graph.nodes[n].get("name", str(n))}"' for n in levels[level]])
                        if len(levels[level]) > 1:
                            f.write(f"    {{ rank = same; {nodes_in_level} }}\n")
                f.write("}\n")
            print(f"[GraphVisualizer] Arquivo .dot customizado salvo em '{dot_filename}'")
        except Exception as e:
            print(f"ERRO ao escrever o arquivo .dot customizado: {e}")
            return
        
        try:
            from graphviz import Source
            s = Source.from_file(dot_filename)
            s.render(output_image_filename, format='png', view=False, cleanup=True)
            print(f"[GraphVisualizer] Imagem do layout lógico salva em '{output_image_filename}.png'")
        except Exception as e:
           print(f"ERRO ao gerar imagem com Graphviz: {e}")

    @staticmethod
    def generate_debug_dot_and_image(graph: nx.DiGraph, dot_filename: str, output_image_filename: str):
        """
        NOVO: Gera um arquivo .dot para depuração.
        """
        # (Este método permanece inalterado)
        if not graph or not graph.nodes:
            return

        node_list = sorted(list(graph.nodes()))
        node_to_name = {node: f"n{i}" for i, node in enumerate(node_list)}
        
        levels = defaultdict(list)
        try:
            temp_graph_for_levels = graph.copy()
            for node in nx.topological_sort(temp_graph_for_levels):
                level = 0
                for pred in temp_graph_for_levels.predecessors(node):
                    level = max(level, temp_graph_for_levels.nodes[pred].get('level', -1) + 1)
                temp_graph_for_levels.nodes[node]['level'] = level
                levels[level].append(node)
        except nx.NetworkXUnfeasible:
            levels.clear()

        try:
            with open(dot_filename, "w", encoding="utf-8") as f:
                f.write("digraph {\n")
                f.write("    rankdir=TB;\n")
                f.write("    node [shape=box, style=rounded];\n\n")

                for node, name in node_to_name.items():
                    f.write(f'    {name} [label="{node}"];\n')
                f.write("\n")

                for src, dst in sorted(graph.edges()):
                    f.write(f'    {node_to_name[src]} -> {node_to_name[dst]};\n')
                f.write("\n")

                if levels:
                    for level in sorted(levels.keys()):
                        nodes_in_level = " ".join([node_to_name[n] for n in levels[level]])
                        if len(levels[level]) > 1:
                            f.write(f"    {{ rank = same; {nodes_in_level} }}\n")
                f.write("}\n")
            print(f"[GraphVisualizer] Arquivo .dot de depuração salvo em '{dot_filename}'")
        except Exception as e:
            print(f"ERRO ao escrever o arquivo .dot de depuração: {e}")
            return

        try:
            from graphviz import Source
            s = Source.from_file(dot_filename)
            s.render(output_image_filename, format='png', view=False, cleanup=True)
            print(f"[GraphVisualizer] Imagem de depuração salva em '{output_image_filename}.png'")
        except Exception as e:
            print(f"ERRO ao gerar imagem de depuração com Graphviz: {e}")
