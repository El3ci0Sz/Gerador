from src.utils.Mapping import Mapping
import random

class Placement_CGRA:
    def __init__(self,mapping: Mapping, cgra_dim , dfg_tam : int, II : int) -> None:
        
        self.dfg_tam = dfg_tam
        self.II = II
        self.cgra_dim = cgra_dim
        self.mapping = mapping
        self.get_placement()
         

    def get_placement(self):
        """
        Realiza o placement aleatório dos nós no CGRA.

        Args:
            mapping (Mapping): Objeto contendo dados do mapeamento.

        Raises:
            ValueError: Se a capacidade do CGRA for insuficiente.
        """
        rows, cols = self.cgra_dim
        max_positions = rows * cols * self.II

        if max_positions < self.dfg_tam:
            raise ValueError("Capacidade insuficiente!!")

        available_positions = [
            (row, col, cycle)
            for row in range(rows)
            for col in range(cols)
            for cycle in range(self.II)
        ]
        random.shuffle(available_positions)
        for node in range(self.dfg_tam):
            if not available_positions:
                raise ValueError(f"Capacidade insuficiente!!")
            self.mapping.placement[node] = available_positions.pop()

