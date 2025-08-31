from src.qca.grammar import Grammar
from src.qca.qca_util import QCA_UTIL

class QCARouting:
    """
    Classe controladora que orquestra o processo de geração de mapeamentos QCA.
    Ela utiliza a classe Grammar para executar os passos de construção do grafo
    de forma organizada e configurável.
    """
    def __init__(self, grid_size: tuple, number_steps: int):
        """
        Inicializa o controlador de roteamento.

        Args:
            grid_size (tuple): As dimensões da grade (ex: (10, 10)).
            number_steps (int): O número de passos para a geração do núcleo do circuito.
        """
        if not isinstance(grid_size, tuple) or len(grid_size) != 2:
            raise ValueError("grid_size must be a tuple of two integers.")
        if not isinstance(number_steps, int) or number_steps <= 0:
            raise ValueError("generation_steps must be a positive integer.")
            
        self.grid_size = grid_size
        self.generation_steps = number_steps
        self.grammar = Grammar(self.grid_size)
        self.graph = None 
        self.qca_utils = QCA_UTIL()
        

        print(f"QCARouting inicializado com grade {self.grid_size} e {self.generation_steps} passos de geração.")

    def generate_layout(self):
        """
        Executa o fluxo geração do layout:

        Returns:
            networkx.DiGraph: O grafo final gerado.
        """
        print("\n--- FASE 1: GERANDO O CIRCUITO PRINCIPAL ---")
        current_pos = self.grammar.first_placement()

        if current_pos:
            for i in range(self.generation_steps):
                next_pos = self.grammar.generate_pattern(current_pos)
                
                if next_pos is None:
                    print(f"Nó {current_pos} não pode ser expandido. Procurando outro ponto...")
                    current_pos = self.grammar.get_random_active_node()
                    if not current_pos:
                        print("Geração do miolo concluída: não há mais pontos de expansão.")
                        break
                else:
                    current_pos = next_pos
        
        print("\n--- FASE 2: FINALIZANDO O MAPEAMENTO ---")

        print("\nExecutando o passo de Merge...")
        self.grammar.merge()

        print("\nExecutando Sincronização e Extensão de Bordas de I/O...")
        self.grammar.synchronize_io_and_extend_to_border()
        
        # Armazena o grafo final e o retorna
        self.graph = self.grammar.graph
        print("\nLayout gerado com sucesso.")
        return self.graph

    def get_generated_graph(self):
        """ Retorna o grafo gerado. """
        if self.graph is None:
            print("AVISO: O grafo ainda não foi gerado. Chame generate_layout() primeiro.")
        return self.graph

