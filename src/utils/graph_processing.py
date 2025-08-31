from src.utils.Mapping import Mapping
from collections import deque

class Graph_Processing:

   def __init__(self, mapping:Mapping, dfg_tam) -> None:
      self.mapping = mapping 
      self.dfg_tam = dfg_tam

   def is_valid(self):
      mapping = self.mapping
      return(self.is_connected(mapping) and not self.has_cycle(mapping.dfg_edges) and self.is_balanced(mapping))

   def is_balanced(self, mapping:Mapping):

      """
        Verifica se os predecessores de cada nó no DFG estão no mesmo nível.

        Args:
            mapping (Mapping): Objeto contendo os vértices e arestas do DFG.

        Returns:
            bool: True se todos os predecessores de cada nó estiverem no mesmo nível, False caso contrário.

        Raises:
            ValueError: Se o DFG apresentar ciclos.
        """

      predecessors, levels = self.calculate_predecessors_and_levels(mapping.dfg_edges)

      for node in mapping.dfg_vertices:
         preds = predecessors[node]
         if preds:
            pred_levels = {levels[pred] for pred in preds}
            if len(pred_levels) > 1:
               return False
      return True

   @staticmethod
   def calculate_predecessors_and_levels(dfg_edges):

      """
        Calcula os predecessores e os níveis de cada nó no grafo de fluxo de dados (DFG).

        Args:
            dfg_edges (dict): Dicionário onde as chaves são nós e os valores são listas
                              de nós destino representando as arestas do DFG.

        Returns:
            tuple: Um dicionário com os predecessores de cada nó e um dicionário com os
                   níveis de cada nó no DFG.

        Raises:
            ValueError: Se forem detectados ciclos no DFG.
        """

      predecessors = {node: [] for node in dfg_edges}
      levels = {}

      for node, edges in dfg_edges.items():
         for dest in edges:
            predecessors[dest].append(node)

      aux_predecessors = {node: preds.copy() for node, preds in predecessors.items()}

      nodes_without_predecessors = deque(node for node, preds in aux_predecessors.items() if not preds)
      visited = set() 
      current_level = 0

      while nodes_without_predecessors:
         next_nodes = deque()
         for node in nodes_without_predecessors:
            if node in visited:
               continue
            visited.add(node)
            levels[node] = current_level

            for dest in dfg_edges.get(node, []):
               aux_predecessors[dest].remove(node)
               if not aux_predecessors[dest]:
                  next_nodes.append(dest)

            nodes_without_predecessors = next_nodes
            current_level += 1


      nodes_in_cycles = set(dfg_edges.keys()) - visited
      if nodes_in_cycles:
         raise ValueError(f"Ciclo detectado nos nós: {nodes_in_cycles}")

      return predecessors, levels

   def has_cycle(self, dfg_edges):
        """
        Detecta se há ciclos em um grafo direcionado.

        Args:
            dfg_edges (dict): Dicionário de adjacência representando o grafo.

        Returns:
            bool: True se houver ciclo, False caso contrário.
        """
        visited = set()
        stack = set()

        def dfs(node, path):
            if node in stack:
                return True, path + [node]
            if node in visited:
                return False, []

            visited.add(node)
            stack.add(node)

            for neighbor in dfg_edges.get(node, []):
                has_cycle, cycle_path = dfs(neighbor, path + [node])
                if has_cycle:
                    return True, cycle_path

            stack.remove(node)
            return False, []

        for node in dfg_edges.keys():
            has_cycle, cycle_path = dfs(node, [])
            if has_cycle:
                return True

        return False

   def is_connected(self, mapping: Mapping):
      """
        Verifica se o grafo DFG está completamente conectado.

        Args:
            mapping (Mapping): Objeto contendo dados do mapeamento.

        Returns:
            bool: True se o DFG for conectado, False caso contrário.
        """
      if not mapping.dfg_edges:
         return False

      visited = set()

      def dfs(node):
         """
            Realiza busca em profundidade para verificar conectividade.
            """
         if node not in visited:
            visited.add(node)
            for neighbor in mapping.dfg_edges[node]:
               dfs(neighbor)

      start_node = next(iter(mapping.dfg_edges))
      dfs(start_node)
      return len(visited) == self.dfg_tam

