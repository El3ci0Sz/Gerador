import numpy as np

class CGRA:
    '''
    Classe que representa um CGRA, com atributos uteis e um metodo para criação do CGRA.

    inputs:
        cgra_dim (tupla): Representa as dimensões de um CGRA,
        arch_name(string): Nome da arquitetura.
    '''

    def __init__(self,cgra_dim, arch_name):
        self.cgra_dim = cgra_dim
        self.arch_name = arch_name
        self.matriz, self.edges = self.faz_matriz()

    '''
    Metodo:
        Apartir de uma dimensão dada, uma matriz é gerada com todas as posições inicialmente com -1.
        Apartir das posições do CGRA, a lógica verifica as conexões horizontais e verticais validas, e armazena
        em uma lista.

    output:
        matriz_cgra (matriz) : Matriz que representa um cgra, posições inicializadas com -1.
        edges (list(tupla)) : 
    '''
    def faz_matriz(self):
        linhas, colunas = self.cgra_dim
        matriz_cgra = np.full((linhas, colunas), -1, dtype=int)
        edges = []


        for l in range(linhas):
            for c in range(colunas):
                if l + 1 < linhas:
                    edges.append(((l, c), (l + 1, c)))
                if c + 1 < colunas:
                    edges.append(((l, c), (l, c + 1)))
        return matriz_cgra, edges