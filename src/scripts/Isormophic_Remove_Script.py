import os
import networkx as nx
from networkx.algorithms.isomorphism import GraphMatcher

def load_graph_from_dot(file_path):
    """
        Carrega um grafo a partir de um arquivo .dot .

        file_path: Caminho para o arquivo .dot.
    """
    try:
        return nx.drawing.nx_pydot.read_dot(file_path)
    except Exception as e:
        print(f"Erro ao carregar {file_path}: {e}")
        return None

def find_dot_files(folder_path):
    """
        Encontra todos os arquivos .dot dentro do diretório, incluindo subdiretórios.

        folder_path: Caminho para a pasta raiz da busca.

        Retorna uma lista com os caminhos completos dos arquivos .dot encontrados.
    """
    dot_files = []
    for root, _, files in os.walk(folder_path): 
        for file in files:
            if file.endswith(".dot"):
                dot_files.append(os.path.join(root, file))
    return dot_files

def remove_isomorphic_graphs_in_folder(folder_path):
    """
        Remove grafos isomorfos dentro de uma pasta, incluindo subdiretórios.
    
        folder_path: Caminho para a pasta raiz da busca.
    """
    graph_files = find_dot_files(folder_path) 
    graphs = []
    graphs_to_remove = set()

    for file_path in graph_files:
        graph = load_graph_from_dot(file_path)
        if graph is None:
            continue
        
        is_isomorphic = False
        for existing_graph in graphs:
            if GraphMatcher(existing_graph, graph).is_isomorphic():
                is_isomorphic = True
                graphs_to_remove.add(file_path)
                break
        
        if not is_isomorphic:
            graphs.append(graph)
    
    for file in graphs_to_remove:
        os.remove(file)
        print(f"Removido: {file}")

    print("Processo concluído. Grafos isomorfos removidos.")

def remove_isomorphic_graphs_between_folders(dir1, dir2):
    """
        Verifica e remove grafos isomorfos do segundo diretório, se também existirem no primeiro diretório.

        dir1: Diretório de referência (não sofre alterações).
        dir2: Diretório do qual os grafos isomorfos serão removidos.
    """
    print(f"Analisando grafos entre '{dir1}' e '{dir2}'...")

    graphs_dir1 = [load_graph_from_dot(file) for file in find_dot_files(dir1)]
    files_dir2 = find_dot_files(dir2)

    graphs_dir1 = [g for g in graphs_dir1 if g is not None]
    graphs_to_remove = set()

    for file_path in files_dir2:
        graph = load_graph_from_dot(file_path)
        if graph is None:
            continue
        
        for existing_graph in graphs_dir1:
            if GraphMatcher(existing_graph, graph).is_isomorphic():
                graphs_to_remove.add(file_path)
                break
    
    for file in graphs_to_remove:
        os.remove(file)
        print(f"Removido: {file}")

    print(f"Processo concluído. Grafos isomorfos removidos de {dir2}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        remove_isomorphic_graphs_in_folder(sys.argv[1])
    elif len(sys.argv) == 3:
        remove_isomorphic_graphs_between_folders(sys.argv[1], sys.argv[2])
    else:
        print("Uso:")
        print("  Para remover isomorfos dentro de um diretório: python script.py <diretorio>")
        print("  Para remover isomorfos entre dois diretórios: python script.py <diretorio_1> <diretorio_2>")
    
