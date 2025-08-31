from src.cgra import interconnection
from src.cgra.placement_cgra import Placement_CGRA
from src.utils.routing import Routing
from src.cgra.interconnection import Interconnection
from src.utils.Mapping import Mapping
from src.utils.graph_processing import Graph_Processing

class Mapping_generator_CGRA:
    """
    Classe responsável por gerar e verificar mapeamentos aleatórios de um DFG para um CGRA.
    """

    def __init__(self, dfg_tam, II, alpha, alpha2, cgra_dim, bits):
      """
        Inicializa os parâmetros necessários para o mapeamento.

        Args:
            dfg_tam (int): Número de nós no DFG.
            II (int): Intervalo de inicialização (Initiation Interval) do CGRA.
            alpha (float): Probabilidade de criar conexões adicionais.
            alpha2 (float): Probabilidade de remover conexões existentes.
            cgra (CGRA): Objeto representando a arquitetura do CGRA.
        """
      self.dfg_tam = dfg_tam
      self.II = II
      self.alpha = alpha
      self.alpha2 = alpha2
      self.cgra_dim = cgra_dim
      self.bits = bits
      self.interconnection = Interconnection(self.cgra_dim,self.bits,self.II)
      self.cgra_graph = self.interconnection.get_graph()

    def mapp(self, max_attempts=200000):
      """
        Realiza o mapeamento completo (placement + routing) do DFG no CGRA,
        garantindo que o mapeamento seja balanceado.

        Args:
            max_attempts (int): Número máximo de tentativas para encontrar um mapeamento balanceado.

        Returns:
            Mapping: Objeto contendo o mapeamento gerado.

        Raises:
            ValueError: Se o número máximo de tentativas for atingido sem encontrar um mapeamento balanceado.
        """

        
      for attempt in range(max_attempts):
         mapping = Mapping(self.dfg_tam)
         Placement_CGRA(mapping,self.cgra_dim,self.dfg_tam,self.II)
         Routing_class = Routing(mapping,self.dfg_tam,self.alpha,self.alpha2,self.cgra_graph)
         Routing_class.get_routing_path()
         if Graph_Processing(mapping, self.dfg_tam).is_valid():
            return mapping
      raise ValueError(f"Não foi possível encontrar um mapeamento balanceado após {max_attempts} tentativas.")
    

  

           
    
