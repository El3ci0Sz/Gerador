class Mapping:
  def __init__(self,num_vertices):
    self.routing = {}
    self.placement: dict = {}
    self.dfg_edges: dict = {}
    self.dfg_vertices = list(range(num_vertices)) 
    self.dfg_num_edges = 0
