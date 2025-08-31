import os
import networkx as nx
import pydot
from networkx.drawing.nx_pydot import read_dot, to_pydot

def find_dot_files(folder_path):
    """
        Encontra todos os arquivos .dot dentro do diretório, incluindo subdiretórios.

        Args:
            folder_path: Caminho para a pasta raiz da busca.
        Returns:
            Retorna uma lista de tuplas, com os caminhos completos dos arquivos .dot e o nome dele.
    """
    dot_files = []
    for root, _, files in os.walk(folder_path): 
        for file in files:
            if file.endswith(".dot"):
                dot_files.append((os.path.join(root, file), file))
    return dot_files


def get_levels(Graph):
    """
        Args:
            Graph: Grafo gerado apartir de um arquivo .dot .
        Returns:
            levels (list): Retorna uma lista contendo o nivel que cada nó do Grafo.
    """
    levels = {}
    for node in nx.topological_sort(Graph):
        preds = list(Graph.predecessors(node))
        levels[node] = (max([levels[p] for p in preds]) + 1) if preds else 0
    return levels

def balance_graph(Graph):

    """
        Insere nós intermediários para balancear o grafo.

        Args:
            Graph: Grafo gerado apartir de um arquivo .dot .
        Returns:
            new_Graph: Retorna o grafo balanceado, mantendo os atributos dos vertices e das arestas.
    """
    levels = get_levels(Graph)
    new_Graph = nx.DiGraph()
    node_counter = 0 

    for node, attrs in Graph.nodes(data=True):
        new_Graph.add_node(node, **attrs) 

    for u, v, attrs in Graph.edges(data=True):
        level_u, level_v = levels[u], levels[v]
        prev = u
        if level_v - level_u > 1:
            num_new_nodes = level_v - level_u - 1
            prev = u
            for i in range(num_new_nodes):
                new_node = f"aux_{node_counter}"
                new_Graph.add_node(new_node, operand="Routing")    
                new_Graph.add_edge(prev, new_node,  **attrs)
                prev = new_node
                node_counter += 1
            new_Graph.add_edge(prev, v, **attrs)
        else:
            new_Graph.add_edge(u, v, **attrs)

    return new_Graph

def save_graph_dot(Graph, output_path):
    """
        Args:
            Graph: Grafo gerado apartir de um arquivo .dot, já balanceado.
            output_path: Caminho para o diretorio de destino.
        Returns: 
            Salva o grafo balanceado em um arquivo .dot, no diretorio de destino.
    """
    pydot_graph = to_pydot(Graph)
    pydot_graph.write(output_path)

def save_graph_image(Graph, output_path):
    """
        Args:
            Graph: Grafo gerado apartir de um arquivo .dot, já balanceado.
            output_path: Caminho para o diretorio de destino.
        Returns:
            Salva o grafo balanceado em imagem .png, no diretorio de destino.
    """
    pydot_graph = to_pydot(Graph)
    pydot_graph.write_png(output_path)

def Balancing(input_dir, output_dir):
    """
        Args:
            input_dir: Diretorio de origem, no qual esta os grafos que serão balanceados.
            output_dir: Diretorio de destino, no qual serão salvos os grafos balanceados.
        Returns:
            Pega todos os grafos (.dot) do dir de origem, depois de balanceados, gera um .dot e uma imagem do grafo balanceado.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    graph_files = find_dot_files(input_dir)

    for file_path, file in graph_files:
            input_path = os.path.join(file_path)
            output_path = os.path.join(output_dir, file)
            img_output_path = os.path.join(output_dir, file.replace(".dot", ".png"))
            
            try:
                Graph = nx.DiGraph(nx.nx_pydot.read_dot(input_path))
                balanced_Graph = balance_graph(Graph)
                
                save_graph_dot(balanced_Graph, output_path)
                save_graph_image(balanced_Graph, img_output_path)
                
                print(f"Processado: {file}")
            except Exception as e:
                print(f"Erro ao processar {file}: {e}")


if __name__ == "__main__":
    import sys
    Balancing(sys.argv[1], sys.argv[2])
