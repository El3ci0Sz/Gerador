import numpy as np
import argparse
import random
from src.mapping_utils.mapping_generator_CGRA_Grammar import Mapping_generator_CGRA_Grammar

def analyze_grammar(params, num_runs=10):
    """
    Executa a geração da gramática 'num_runs' vezes para um número fixo de passos
    e reporta o tamanho médio, mínimo e máximo do grafo resultante.
    """
    # A CORREÇÃO ESTÁ NESTA LINHA: params['steps'] em vez de params['grammar_steps']
    steps_to_test = params['steps']
    
    print(f"\n--- Analisando para um máximo de {steps_to_test} passos ---")
    print(f"Parâmetros: max_path={params['max_path_length']}, balance={params['balance_paths']}, extend_io={not params['no_extend_io']}")
    
    final_node_counts = []
    for i in range(num_runs):
        try:
            current_steps = random.randint(1, steps_to_test)
            cgra_gen = Mapping_generator_CGRA_Grammar(
                cgra_dim=(8, 8), II=4, bits='1000', k_range=[2, 4],
                grammar_steps=current_steps,
                no_extend_io=params['no_extend_io'],
                max_path_length=params['max_path_length'],
                balance_paths=params['balance_paths']
            )
            final_graph = cgra_gen.mapp(min_nodes=1)
            if final_graph:
                final_node_counts.append(final_graph.number_of_nodes())

        except Exception as e:
            # Ignora falhas para focar nas execuções bem-sucedidas
            pass 

    if not final_node_counts:
        print("Nenhum grafo foi gerado com sucesso para esta configuração.")
        return

    print("---------------------------------")
    print(f"Resultados para um máximo de {steps_to_test} passos:")
    print(f"  - Execuções bem-sucedidas: {len(final_node_counts)}/{num_runs}")
    print(f"  - Média de Nós: {np.mean(final_node_counts):.2f}")
    print(f"  - Mínimo de Nós: {np.min(final_node_counts)}")
    print(f"  - Máximo de Nós: {np.max(final_node_counts)}")
    print("---------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script para analisar o impacto dos parâmetros da gramática.')
    
    parser.add_argument(
        '--steps', 
        type=int, 
        default=10, 
        help='Número máximo de grammar_steps para sortear.'
    )
    
    parser.add_argument(
        '--no_extend_io', 
        action='store_true', 
        help='Se presente, desativa a etapa de extensão de I/O para a borda.'
    )
    
    parser.add_argument(
        '--max_path_length', 
        type=int, 
        default=15, 
        help='Comprimento máximo para os caminhos.'
    )

    parser.add_argument(
        '--balance_paths', 
        action='store_true', 
        help='Tenta gerar caminhos de mesmo comprimento.'
    )

    args = parser.parse_args()

    analyze_grammar(vars(args))
