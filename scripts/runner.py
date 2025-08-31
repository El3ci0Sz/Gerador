# scripts/runner.py

import argparse
import logging
import os
import time
import sys

from concurrent.futures import ProcessPoolExecutor, as_completed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mapping_generator.cli import create_parser
from mapping_generator.generation.controller import GenerationTask, generate_recipes
from scripts.post_process_cleaner import run_cleaning_process

def run_single_generation(args):
    """Executes a single, specific generation task based on parsed arguments."""
    print("--- Running Single Generation Task ---")
    
    recipe = None
    if args.tec == 'cgra' and args.gen_mode == 'grammar':
        all_recipes = generate_recipes(args.difficulty)
        recipe = all_recipes.get(args.difficulty)
        if not recipe:
            print(f"Error: Invalid difficulty level '{args.difficulty}'. Please choose a valid level.")
            return

    task_params = {
        'tec': args.tec, 'gen_mode': args.gen_mode, 'k': args.k_graphs,
        'difficulty': args.difficulty, 'arch_sizes': [tuple(args.arch_size)],
        'cgra_params': {'bits': args.bits}, 'graph_range': tuple(args.graph_range),
        'recipe': recipe, 'k_range': tuple(args.k_range), 'no_extend_io': args.no_extend_io,
        'max_path_length': args.max_path_length, 'no_images': args.no_images,
        'qca_arch': args.qca_arch, 'ii': args.ii, 'output_dir': args.output_dir,
        'alpha': args.alpha, 'retries_multiplier': args.retries_multiplier
    }

    task = GenerationTask(**task_params)
    task.run()
    print("--- Single Generation Task Finished ---")

def run_campaign_generation(args):
    """Executes the full, parallel campaign to generate a large dataset."""
    print("--- Running Campaign Generation ---")
    
    GRAPHS_PER_DIFFICULTY = 500
    MAX_DIFFICULTY = 20
    GRAPH_SIZES_TO_GENERATE = list(range(3, 17))
    ARCH_SIZES = [(4, 4), (8, 8)]
    BIT_CONFIGS = ['1000', '1111']
    GRAPHS_PER_DIFFICULTY_SMALL = 50
    recipes = generate_recipes(MAX_DIFFICULTY)

    tasks_params_list = []
    for size in GRAPH_SIZES_TO_GENERATE:
        for arch in ARCH_SIZES:
            for bits in BIT_CONFIGS:
                num_graphs = GRAPHS_PER_DIFFICULTY if size > 5 else GRAPHS_PER_DIFFICULTY_SMALL
                for difficulty, recipe in recipes.items():
                    tasks_params_list.append({
                        'tec': 'cgra', 'gen_mode': 'grammar', 'k': num_graphs,
                        'difficulty': difficulty, 'arch_sizes': [arch],
                        'cgra_params': {'bits': bits}, 'graph_range': (size, size),
                        'recipe': recipe, 'k_range': (2, 3), 'no_extend_io': False,
                        'max_path_length': 15, 'no_images': args.no_images, 
                        'qca_arch': 'U', 'ii': None, 'output_dir': args.output_dir,
                        'alpha': 0.3, 'retries_multiplier': 150
                    })
    
    print(f"Campaign Defined. Total of {len(tasks_params_list)} generation tasks to be executed.")
    
    start_time = time.time()
    max_cores = os.cpu_count()
    print(f"Starting ProcessPoolExecutor with {max_cores} workers...")

    with ProcessPoolExecutor(max_workers=max_cores) as executor:
        futures = [executor.submit(run_task_in_worker, params) for params in tasks_params_list]
        
        for i, future in enumerate(as_completed(futures)):
            print(f"Generation Progress: {i+1}/{len(tasks_params_list)} tasks completed.")
            try:
                future.result()
            except Exception as e:
                logging.critical(f"A worker task generated a fatal error: {e}", exc_info=True)

    end_time = time.time()
    print(f"\n--- CAMPAIGN GENERATION COMPLETE ---")
    print(f"Total generation time: {(end_time - start_time) / 60:.2f} minutes.")

    if args.clean:
        print("\n--- STARTING AUTOMATIC ISOMORPHISM CLEANING ---")
        source_dir = args.output_dir
        cleaned_dir = f"{source_dir}_cleaned"
        run_cleaning_process(source_dir, cleaned_dir)

def run_task_in_worker(task_params):
    """Helper function to instantiate and run GenerationTask in a worker process."""
    task = GenerationTask(**task_params)
    return task.run()

def main():
    """Main function to set up CLI, parse arguments, and launch the correct mode."""
    parser = create_parser()
    args = parser.parse_args()

    log_level = logging.DEBUG if hasattr(args, 'verbose') and args.verbose else logging.WARNING
    logging.basicConfig(level=log_level, format='[%(levelname)s][%(name)s] %(message)s')

    if args.command == 'single':
        run_single_generation(args)
    elif args.command == 'campaign':
        run_campaign_generation(args)

if __name__ == "__main__":
    main()
