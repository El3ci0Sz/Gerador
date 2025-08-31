from src.cgra.mapping_generator_CGRA import Mapping_generator_CGRA

from src.qca import qca_util

from src.utils.Graph_Visualizer import Graph_Visualizer

from src.qca.qca_routing import QCARouting

from src.qca.qca_util import QCA_UTIL

from math import ceil

import argparse

import random

import os


class Mapp_Controler:


   #0 cgra, 1 qca

   @staticmethod

   def get_parameters():


      parser = argparse.ArgumentParser(description='Gerar mapeamentos de grafos para CGRA e QCA.')

      parser.add_argument('--k', type=int, default=2, help='Número de grafos a gerar.')

      parser.add_argument('--tec', type=str, default='0', choices=['0', '1'], help='Tecnologia: 0 = CGRA, 1 = QCA.')

      parser.add_argument('--tam_arch', type=int, nargs='+', default=[4, 4, 8, 8], help='Tamanhos de arquitetura (ex: 4 4 8 8).')


      # --- Parâmetros CGRA ---

      parser.add_argument('--graph_range', type=int, nargs=2, default=(10, 20), help='[CGRA] Intervalo de tamanhos de grafos.')

      parser.add_argument('--alpha', type=float, default=0.8, help='[CGRA] Valor de alpha.')

      parser.add_argument('--alpha2', type=float, default=0.4, help='[CGRA] Valor de alpha2.')

      parser.add_argument('--bits', type=str, default='1000', help='[CGRA] Bits de interconexão.')


      # --- Parâmetros QCA ---

      parser.add_argument('--qca_steps', type=int, default=50, help='[QCA] Número de passos de geração para a gramática QCA.')

      args = parser.parse_args()

      

      tam_arch = [(args.tam_arch[i], args.tam_arch[i+1]) for i in range(0, len(args.tam_arch), 2)]

      

      Mapp_Controler.mapping(args.k, tuple(args.graph_range), tam_arch, args.alpha, args.alpha2, args.bits, args.tec, args.qca_steps)


   @staticmethod

   def mapping(k, graph_range, tam_arch,alpha, alpha2, bits, tecnology, qca_steps):

      if tecnology == "0":
         initial , final = graph_range
         num_graphs = 0

         while num_graphs < k:

            num_vertices = random.randint(initial, final)
            row , col = random.choice(tam_arch)
            II = ceil(num_vertices/(row * col))

            if row * col < num_vertices:

               print(f"[AVISO] Arquitetura {row}x{col} não suporta {num_vertices} vértices. Pulando.")
               continue

            mapping_generator = Mapping_generator_CGRA(num_vertices, II, alpha, alpha2, (row,col), bits)

            try:
                  mapping = mapping_generator.mapp()

            except ValueError as e:
                  continue

            num_edges = sum(len([v for v in targets if v in mapping.dfg_vertices]) for targets in mapping.dfg_edges.values())

            directory = f"mappings/{row}x{col}/{num_vertices}/{num_edges}"
            os.makedirs(directory, exist_ok=True)
            path = f"{directory}/graph_{num_vertices}_{num_edges}.dot"
            graph_name = f"graph_{num_vertices}_{num_edges}"           #Graph_Visualizer.plot_cgra(mapping,(row,col),routing=False,output_file="output.png")            
            Graph_Visualizer.export_to_dot(mapping, path)
            print(f"Mapa {num_graphs+1}/{k} salvo em {path}")
            Graph_Visualizer.generate_image_from_dot(path)
            Graph_Visualizer.export_to_json(mapping,graph_name,path)
            num_graphs += 1

            

      if tecnology == "1":

         

         for i in range(k):

            # Escolhe um tamanho de arquitetura aleatório da lista fornecida

            grid_size = random.choice(tam_arch)

            row, col = grid_size


            print(f"\nGerando Mapeamento QCA {i+1}/{k} para grade {grid_size} com {qca_steps} passos...")


            # 1. Cria uma instância do nosso controlador QCARouting

            router = QCARouting(grid_size,qca_steps)


            # 2. Executa a geração completa do layout

            final_graph = router.generate_layout()


            if not final_graph or not final_graph.nodes:

              print("AVISO: Falha ao gerar um grafo válido. Pulando para o próximo.")

              continue


            # 3. Define o diretório de saída com base nas propriedades do grafo gerado

            num_nodes = len(final_graph.nodes)

            num_edges = len(final_graph.edges)

            directory = f"mappings_qca/{row}x{col}/{num_nodes}_nodes_{num_edges}_edges"

            os.makedirs(directory, exist_ok=True)


            # 4. Salva os arquivos de saída

            print(f"--- Salvando resultados em '{directory}' ---")


            # Salva a imagem do layout físico

            path_matplotlib = f"{directory}/qca_fisico_{i+1}.png"

            QCA_UTIL.save_graph_image(final_graph,path_matplotlib)


            # Salva a imagem do layout lógico e o arquivo .dot

            path_base_graphviz = f"{directory}/qca_logico_{i+1}"

            QCA_UTIL.generate_dot_image(final_graph,f"{path_base_graphviz}.dot", path_base_graphviz)


            print(f"Mapeamento QCA {i+1}/{k} salvo com sucesso.")


if __name__ == "__main__":

   Mapp_Controler.get_parameters() 
