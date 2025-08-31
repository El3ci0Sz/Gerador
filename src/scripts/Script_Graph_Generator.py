import os
import random
import networkx as nx
import argparse
from math import ceil
from src.cgra.cgra import CGRA
from src.utils.mapping_generator import Mapping_generator
from src.utils.Graph_Visualizer import Graph_Visualizer

def script_mapeamentos(k, graph_range, tam_arch,alpha, alpha2):
    """
    Gera e salva um conjunto de mapeamentos de grafos para um CGRA com diferentes
    configurações de arquitetura e número de vértices. Para cada mapeamento gerado,
    o grafo é exportado como um arquivo .dot e uma imagem é gerada.

    Args:
        k (int): Número de mapeamentos a serem gerados.
        graph_range (tuple): Intervalo de número de vértices do grafo (min, max).
        tam_arch (list): Lista de tuplas, que são intervalo de arquiteturas possiveis do CGRA.
        alpha (float): Parâmetro alpha.
        alpha2 (float): Segundo parâmetro alpha.
    """
    initial , final = graph_range
    num_graphs = 0
    
    while num_graphs < k:
        num_vertices = random.randint(initial, final)
        
        row , col = random.choice(tam_arch)
        cgra = CGRA((row, col), "Script")
        II = ceil(num_vertices/(row * col))

        mapping_generator = Mapping_generator(num_vertices, II, alpha, alpha2, cgra)
        
        try:
            mapping = mapping_generator.mapp()
        except ValueError as e:
            continue

        num_edges = sum(len([v for v in targets if v in mapping.dfg_vertices]) for targets in mapping.dfg_edges.values())

        directory = f"mappings/{row}x{col}/{num_vertices}/{num_edges}"
        os.makedirs(directory, exist_ok=True)
        path = f"{directory}/graph_{num_vertices}_{num_edges}.dot"
        
        Graph_Visualizer.export_to_dot(mapping, path)
        print(f"Mapa {num_graphs+1}/{k} salvo em {path}")
        Graph_Visualizer.generate_image_from_dot(path)
        num_graphs += 1


def main():
    parser = argparse.ArgumentParser(description='Gerar mapeamentos de grafos.')
    parser.add_argument('--k', type=int, default=5, help='Número de grafos a gerar.')
    parser.add_argument('--graph_range', type=int, nargs=2, default=(2, 5), help='Intervalo de tamanhos de grafos.')
    parser.add_argument('--tam_arch', type=int, nargs='+', default=[4, 4, 8, 8], help='Tamanhos possíveis de arquitetura (ex: 4x4 8x8).')
    parser.add_argument('--alpha', type=float, default=0.8, help='Valor de alpha.')
    parser.add_argument('--alpha2', type=float, default=0.4, help='Valor de alpha2.')
    
    args = parser.parse_args()
    
    tam_arch = [(args.tam_arch[i], args.tam_arch[i+1]) for i in range(0, len(args.tam_arch), 2)]
    
    script_mapeamentos(args.k, tuple(args.graph_range), tam_arch, args.alpha, args.alpha2)

if __name__ == "__main__":
    main()
