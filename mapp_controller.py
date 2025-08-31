import sys
import argparse
import random
import os
from src.mapping_utils.mappingControler import MappingControler

def generate_recipes(max_difficulty):
    """
    Gera dinamicamente um dicionário de receitas com base em um padrão de
    complexidade crescente até um nível de dificuldade máximo.
    """
    recipes = {1: {"reconvergence": 0, "convergence": 0}}
    if max_difficulty == 1:
        return recipes

    r, c = 0, 0
    for i in range(2, max_difficulty + 1):
        if r == c:
            c += 1
        elif c > r:
            r, c = c, r
        elif r > c + 1:
            c += 1
        else: # r == c + 1
            r, c = c, r + 1
        
        recipes[i] = {"reconvergence": r, "convergence": c}
        
    return recipes

class Mapp_Controler:
    """
    Classe original que continha a lógica de execução.
    O método get_parameters agora é usado principalmente para testes standalone,
    enquanto a lógica principal da campanha foi movida para run_campaign.py.
    """
    @staticmethod
    def get_parameters():
        parser = argparse.ArgumentParser(description='Gerador de Mapeamentos para CGRA e QCA.')
        
        parser.add_argument('--max_difficulty', type=int, default=4,
                            help='Nível máximo de dificuldade para gerar (de 1 até este valor).')
        parser.add_argument('--graphs_per_difficulty', type=int, default=100,
                            help='Número de grafos a gerar para CADA nível de dificuldade.')
        parser.add_argument('--gen_mode', type=str, default='grammar', choices=['random', 'grammar'])
        parser.add_argument('--tec', type=str, default='0', choices=['0', '1'])
        parser.add_argument('--tam_arch', type=int, nargs='+', default=[4, 4])
        parser.add_argument('--graph_range', type=int, nargs=2, default=(20, 40))
        parser.add_argument('--bits', type=str, default='1000')
        parser.add_argument('--k_range', type=int, nargs=2, default=[2, 3])
        parser.add_argument('--max_path_length', type=int, default=15)
        parser.add_argument('--qca_arch', type=str, default='U', choices=['U', 'R', 'T'])
        parser.add_argument('--no_extend_io', action='store_true')
        parser.add_argument('--no_images', action='store_true')
        
        args = parser.parse_args()
        tam_arch = [(args.tam_arch[i], args.tam_arch[i+1]) for i in range(0, len(args.tam_arch), 2)]
        
        recipes_to_generate = generate_recipes(args.max_difficulty)
        
        print(f"--- INICIANDO CAMPANHA DE GERAÇÃO (MODO STANDALONE) ---")
        print(f"Dificuldade Máxima: {args.max_difficulty}")
        print(f"Grafos por Dificuldade: {args.graphs_per_difficulty}")
        print(f"Receitas a serem geradas: {recipes_to_generate}")
        print("--------------------------------------")

        for difficulty, recipe in recipes_to_generate.items():
            print(f"\n===== PROCESSANDO DIFICULDADE {difficulty} (Receita: {recipe}) =====")

            controller = MappingControler(
                gen_mode=args.gen_mode,
                tec=args.tec,
                k=args.graphs_per_difficulty,
                difficulty=difficulty,
                tam_arch=tam_arch,
                cgra_params={'bits': args.bits},
                graph_range=tuple(args.graph_range),
                recipe=recipe,
                k_range=tuple(args.k_range),
                no_extend_io=args.no_extend_io,
                max_path_length=args.max_path_length,
                no_images=args.no_images,
                qca_arch=args.qca_arch
            )
            return controller.run()

def run_single_generation_task(task_params: dict):
    """
    Executa uma única tarefa de geração para uma combinação de parâmetros.
    Esta é a função de trabalho chamada pelos processos paralelos.
    """
    # Desempacota os parâmetros da tarefa
    graph_size = task_params['graph_size_min']
    tam_arch = task_params['tam_arch']
    bits = task_params['bits']
    max_difficulty = task_params['max_difficulty']
    graphs_per_difficulty = task_params['graphs_per_difficulty']
    no_images = task_params['no_images']

    print(f"--- INICIANDO TAREFA: Size={graph_size}, Arch={tam_arch}, Bits={bits}, NoImages={no_images} ---")

    recipes_to_generate = generate_recipes(max_difficulty)
    
    for difficulty, recipe in recipes_to_generate.items():
        print(f"  [TAREFA PID:{os.getpid()}] Processando: Size={graph_size}, Arch={tam_arch}, Bits={bits}, Diff={difficulty}")

        controller = MappingControler(
            gen_mode='grammar',
            tec='0',
            k=graphs_per_difficulty,
            difficulty=difficulty,
            tam_arch=[tam_arch],
            cgra_params={'bits': bits},
            graph_range=(graph_size, graph_size),
            recipe=recipe,
            k_range=(2, 3),
            no_extend_io=False,
            max_path_length=15,
            no_images=no_images,
            qca_arch='U'
        )
        
        success = controller.run()
        if not success:
            print(f"AVISO: A tarefa para Size={graph_size}, Arch={tam_arch}, Diff={difficulty} não foi 100% concluída.")

    print(f"--- TAREFA FINALIZADA: Size={graph_size}, Arch={tam_arch}, Bits={bits} ---")
    return True

if __name__ == "__main__":
    print("Este script foi refatorado e agora é projetado para ser chamado por um orquestrador (run_campaign.py).")
    print("Executar este arquivo diretamente não iniciará a campanha completa.")
    print("Usando a função get_parameters() para um teste rápido com argumentos de linha de comando...")
    
    # Para testar, você pode executar: python mapp_controller.py --max_difficulty 2 --graphs_per_difficulty 5
    random.seed()
    success = Mapp_Controler.get_parameters()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
