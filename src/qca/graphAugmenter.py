import networkx as nx
import random
from networkx.algorithms.isomorphism.isomorph import graph_could_be_isomorphic
from networkx.drawing.nx_pydot import read_dot,write_dot

class GraphAugmenter:
  def __init__(self, file_path:str) -> None:
    self.base_graph = self.load_dot_file(file_path) 
    self.graph_name = file_path
    #Ver sobre esse input e output aqui
    #Acredito que seja o formato dos nos la no png e o attr do dot
    self.inputs = [n for n, attr in self.base_graph.nodes(data=True) if  attr.get('shape') in ['box', 'triangle']]
    self.outputs = [n for n, attr in self.base_graph.nodes(data=True) if  attr.get('shape') in ['invtriangle']]
    self.other_nodes = list(set(self.base_graph.nodes()) - set(self.inputs) -  set(self.outputs))


  def load_dot_file(self,file_path: str) -> nx.DiGraph:

    """
      Carrega um grafo a partir de um arquivo .dot usando NetworkX.
      
      Args:
          filepath (str): O caminho para o arquivo .dot.

      Returns:
          nx.DiGraph: Um objeto de grafo do NetworkX.
    """

    try:
      graph = read_dot(file_path)
      print(f"Grafo de {file_path} carregado com sucesso\ninfo:{graph.nodes()} nos e {graph.edges()} arestas")
      return graph

    except Exception as e:
      print(f"Erro ao carregar o arquivo {file_path}: {e}")
      return None

  def get_new_graph_name(self, operation_name : str) -> str:
      """
        Cria um nome para o novo grafo gerado
      """
      return f"{self.graph_name}_{operation_name}"

  def save_to_dot(self, graph: nx.DiGraph, filename:str) -> None:
    """ 
    Salva o grafo em um arquivo .dot
    """
    try:
      write_dot(graph,filename)
      print(f"Grafo salvo em {filename}")
    except Exception as e:
      print(F"Erro ao salvar o arquivo: {e}")

  def remove_random_input(self):
      """
      Remove um nó de entrada aleatrio.
      """
      if not self.inputs:
          print("Nenhum nó de entrada para remover.")
          return None

      node_to_remove = random.choice(self.inputs)
      
      new_graph = self.base_graph.copy()
      new_graph.remove_node(node_to_remove)
      
      unreachable_nodes = []
      for node in list(new_graph.nodes()):
          if new_graph.in_degree(node) == 0 and new_graph.nodes[node].get('shape') not in ['box', 'triangle']:
              unreachable_nodes.append(node)
      
      for unreachable_node in unreachable_nodes:
          descendants = nx.descendants(new_graph, unreachable_node)
          nodes_to_remove_from_graph = {unreachable_node} | descendants
          new_graph.remove_nodes_from(nodes_to_remove_from_graph)
              
      new_graph.graph['name'] = self.get_new_graph_name(f"pruned_input_{node_to_remove}")
      print(f"No removido: {node_to_remove}")
      return new_graph

  
  
