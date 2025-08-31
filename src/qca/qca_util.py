import matplotlib.pyplot as plt
import networkx as nx
from graphviz import Source

class QCA_UTIL:

    @staticmethod
    def calculate_levels(graph):
        """ NOVO MÉTODO: Calcula o nível de cada nó como o caminho mais longo de qualquer entrada. """
        try:
            for node in nx.topological_sort(graph):
                preds = list(graph.predecessors(node))
                if not preds:
                    level = 0
                else:
                    level = max(graph.nodes[p]['level'] for p in preds) + 1
                graph.nodes[node]['level'] = level
        except nx.NetworkXUnfeasible:
            print("ERRO: O grafo possui ciclos, não é possível calcular os níveis. Verifique a função 'merge'.")

    @staticmethod
    def save_graph_image( graph,filename="qca_mapping.png"):
        plt.figure(figsize=(16, 16))
        pos = {node: (node[1], -node[0]) for node in graph.nodes}
        levels = nx.get_node_attributes(graph, 'level')
        labels = {node: f"{node}\nL:{levels.get(node, 'N/A')}" for node in graph.nodes}
        
        nx.draw(graph, pos, labels=labels, with_labels=True, node_color='skyblue', 
                node_size=2000, font_size=10, font_weight='bold', arrows=True,
                arrowstyle='->', arrowsize=20)
        plt.title("QCA Mapping - Layout Físico na Grade")
        plt.savefig(filename)
        plt.close()
        print(f"[graph] Imagem do layout físico salva em {filename}")

    @staticmethod
    def save_to_dot_with_labels(graph,filename="final_mapping.dot"):
        """
        CORRIGIDO: Agora retorna True em caso de sucesso e False em caso de falha.
        """
        g_copy = graph.copy()
        # É preciso calcular os níveis uma última vez antes de salvar
        QCA_UTIL.calculate_levels(graph)
        inputs = [n for n, d in g_copy.in_degree() if d == 0]
        outputs = [n for n, d in g_copy.out_degree() if d == 0]
        
        for node in g_copy.nodes():
            level = graph.nodes[node].get('level', 'N/A')
            
            if node in inputs:
                role, color, shape = "Input", "limegreen", "invhouse"
            elif node in outputs:
                role, color, shape = "Output", "tomato", "house"
            else:
                role, color, shape = "Internal", "skyblue", "ellipse"

            g_copy.nodes[node]['label'] = f"Pos: {node}\nLevel: {level}\nType: {role}"
            g_copy.nodes[node]['color'] = color
            g_copy.nodes[node]['fillcolor'] = color
            g_copy.nodes[node]['style'] = 'filled'
            g_copy.nodes[node]['shape'] = shape
            g_copy.nodes[node]['fontname'] = "Helvetica"

        try:
            nx.drawing.nx_pydot.write_dot(g_copy, filename)
            return True  # <-- **CORREÇÃO: Retorna True em caso de sucesso**
        except ImportError:
            print("[graph] AVISO: Para salvar em .dot, instale pydot e graphviz: pip install pydot graphviz")
            return False # <-- **CORREÇÃO: Retorna False em caso de falha**
        except Exception as e:
            print(f"[graph] ERRO ao tentar salvar o arquivo .dot: {e}")
            return False # <-- **CORREÇÃO: Retorna False em outras falhas**


    @staticmethod
    def generate_dot_image(graph, dot_filename, output_filename, cleanup=True):
        """
        Gera uma imagem a partir do arquivo .dot e, opcionalmente,
        limpa o arquivo .dot intermediário.
        """
        if not QCA_UTIL.save_to_dot_with_labels(graph, dot_filename):
            print("[graphviz] Geração da imagem pulada pois o arquivo .dot não pôde ser criado.")
            return

        print(f"\n[graphviz] Tentando gerar imagem a partir de '{dot_filename}'...")
        try:
            from graphviz import Source
            s = Source.from_file(dot_filename)
            
            s.render(output_filename, format='png', view=False, cleanup=cleanup)
            
            print(f"[graphviz] Imagem do layout lógico salva em '{output_filename}.png'")
        except ImportError:
            print("\n[graphviz] AVISO: Para gerar a imagem, a biblioteca 'graphviz' é necessária (pip install graphviz).")
        except Exception as e:
            print(f"\n[graphviz] ERRO ao gerar imagem: {e}")
            print("  Certifique-se de que o Graphviz (https://graphviz.org/download/) está instalado e no PATH do sistema.")
