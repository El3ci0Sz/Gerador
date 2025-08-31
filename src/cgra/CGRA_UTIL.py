import matplotlib.pyplot as plt
import networkx as nx

class CGRA_UTIL:
    """
    Classe de utilidades para processar e visualizar grafos de CGRA.
    """
    @staticmethod
    def save_cgra_graph_image(graph, filename="cgra_map.png"):
        """
        Salva uma imagem do grafo CGRA gerado pela gramática.
        Usa um layout 2D e cores para representar a dimensão do tempo (II).
        """
        if not graph or not graph.nodes:
            print("[CGRA_UTIL] Grafo vazio, nenhuma imagem para salvar.")
            return

        print(f"[CGRA_UTIL] Gerando imagem do grafo CGRA em {filename}...")
        
        plt.figure(figsize=(16, 16))
        
        # Cria um layout 2D, mas usa cores para a 3ª dimensão (tempo)
        pos = {node: (node[1], -node[0]) for node in graph.nodes}
        
        # Gera uma lista de cores, uma para cada passo de tempo (II)
        max_ii = max(node[2] for node in graph.nodes) if graph.nodes else 0
        colors = plt.cm.viridis([node[2] / (max_ii + 1) for node in graph.nodes])
        
        nx.draw(graph, pos, with_labels=True, node_color=colors,
                node_size=800, font_size=8, font_color='white', font_weight='bold',
                arrows=True, arrowstyle='->', arrowsize=15)
        
        plt.title("Mapeamento CGRA (Gerado por Gramática)")
        plt.savefig(filename)
        plt.close()
        print(f"[CGRA_UTIL] Imagem salva com sucesso.")

    @staticmethod
    def generate_cgra_dot_image(graph, dot_filename, output_filename, cleanup=True):
        """
        Salva o grafo em .dot e gera a imagem com Graphviz.
        """
        if not graph or not graph.nodes:
            print("[CGRA_UTIL] Grafo vazio, nenhum arquivo .dot para salvar.")
            return

        # Para o .dot, podemos simplesmente usar a função padrão do networkx
        try:
            nx.drawing.nx_pydot.write_dot(graph, dot_filename)
            print(f"[CGRA_UTIL] Arquivo .dot salvo em '{dot_filename}'")
        except Exception as e:
            print(f"ERRO ao salvar .dot do CGRA: {e}")
            return # Não continua se o .dot falhar

        # Gera a imagem a partir do .dot
        try:
            from graphviz import Source
            s = Source.from_file(dot_filename)
            s.render(output_filename, format='png', view=False, cleanup=cleanup)
            print(f"[CGRA_UTIL] Imagem Graphviz salva em '{output_filename}.png'")
        except Exception as e:
            print(f"ERRO ao gerar imagem Graphviz para CGRA: {e}")
