import networkx as nx
import pydot

class GraphUtil:
    @staticmethod
    def calculate_levels(graph):
        try:
            for node in nx.topological_sort(graph):
                preds = list(graph.predecessors(node))
                if not preds:
                    level = 0
                else:
                    level = max(graph.nodes[p].get('level', -1) for p in preds) + 1
                graph.nodes[node]['level'] = level
        except nx.NetworkXUnfeasible:
            print("ERRO: O grafo possui ciclos, não é possível calcular os níveis.")

    @staticmethod
    def save_to_dot_with_labels(graph, filename="final_mapping.dot"):
        g_copy = graph.copy()
        GraphUtil.calculate_levels(g_copy)

        node_list = list(g_copy.nodes())
        node_to_name_map = {node: str(i) for i, node in enumerate(node_list)}
        g_relabeled = nx.relabel_nodes(g_copy, node_to_name_map)
        
        pydot_graph = nx.drawing.nx_pydot.to_pydot(g_relabeled)

        levels = {}
        for original_node, new_name in node_to_name_map.items():
            level = g_copy.nodes[original_node].get('level')
            if level is not None:
                if level not in levels: levels[level] = []
                levels[level].append(new_name)

        for level_nodes in levels.values():
            subg = pydot.Subgraph(rank='same')
            for node_name in level_nodes:
                subg.add_node(pydot.Node(node_name))
            pydot_graph.add_subgraph(subg)
            
        for original_node, new_name in node_to_name_map.items():
            node_in_pydot = pydot_graph.get_node(new_name)[0] # Pega o nó
            level = g_copy.nodes[original_node].get('level', 'N/A')
            
            is_input = g_copy.in_degree(original_node) == 0
            is_output = g_copy.out_degree(original_node) == 0

            if is_input: role, color, shape = "Input", "limegreen", "invhouse"
            elif is_output: role, color, shape = "Output", "tomato", "house"
            else: role, color, shape = "Internal", "skyblue", "ellipse"

            node_in_pydot.set_label(f"Pos: {original_node}\nLevel: {level}\nType: {role}")
            node_in_pydot.set_color(color)
            node_in_pydot.set_fillcolor(color)
            node_in_pydot.set_style('filled')
            node_in_pydot.set_shape(shape)
            node_in_pydot.set_fontname("Helvetica")
        
        try:
            pydot_graph.write(filename)
            return True
        except Exception as e:
            print(f"[GraphUtil] ERRO ao tentar salvar o arquivo .dot: {e}")
            return False

    @staticmethod
    def generate_dot_image(graph, dot_filename, output_filename, cleanup=True):
        if not GraphUtil.save_to_dot_with_labels(graph, dot_filename):
            print("[GraphUtil] Geração da imagem pulada pois o arquivo .dot não pôde ser criado.")
            return

        print(f"\n[GraphUtil] Tentando gerar imagem a partir de '{dot_filename}'...")
        try:
            from graphviz import Source
            s = Source.from_file(dot_filename)
            s.render(output_filename, format='png', view=False, cleanup=cleanup)
            print(f"[GraphUtil] Imagem do layout lógico salva em '{output_filename}.png'")
        except ImportError:
            print("\n[GraphUtil] AVISO: Para gerar a imagem, a biblioteca 'graphviz' é necessária (pip install graphviz).")
        except Exception as e:
            print(f"\n[GraphUtil] ERRO ao gerar imagem: {e}")
            print("  Certifique-se de que o Graphviz (https://graphviz.org/download/) está instalado e no PATH do sistema.")
