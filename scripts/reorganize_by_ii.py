# scripts/reorganize_by_ii.py

import os
import shutil
import argparse
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def copy_directory_contents(source_dir: str, dest_dir: str, use_move: bool) -> int:
    """
    Worker function that copies or moves all files from a source to a destination.
    This function processes one entire directory.
    """
    try:
        if not os.path.isdir(source_dir):
            return 0
            
        os.makedirs(dest_dir, exist_ok=True)
        
        file_count = 0
        for filename in os.listdir(source_dir):
            source_file = os.path.join(source_dir, filename)
            dest_file = os.path.join(dest_dir, filename)
            
            if os.path.isfile(source_file):
                if use_move:
                    shutil.move(source_file, dest_file)
                else:
                    shutil.copy2(source_file, dest_file)
                file_count += 1
        return file_count
    except Exception as e:
        logging.error(f"Failed to process directory {source_dir}: {e}", exc_info=True)
        return 0

def main():
    """Finds directories to reorganize and processes them in parallel."""
    parser = argparse.ArgumentParser(
        description="Reorganizes a results directory by separating data based on II value.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("source_dir", help="The root directory with the combined II results.")
    parser.add_argument("dest_dir", help="The new root directory where the filtered results will be saved.")
    parser.add_argument("--ii", required=True, type=int, choices=[1, 2], help="The II value to keep (1 or 2).")
    parser.add_argument("--move", action='store_true', help="Move files instead of copying.")
    args = parser.parse_args()

    source_path = os.path.abspath(args.source_dir)
    dest_path = os.path.abspath(args.dest_dir)

    if not os.path.isdir(source_path):
        print(f"Error: Source directory '{source_path}' does not exist.")
        return

    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
        print(f"Destination directory '{dest_path}' created.")

    tasks = []
    folder_to_keep = f"II_{args.ii}"
    print(f"Scanning '{source_path}' to find all '{folder_to_keep}' directories...")

    # Passo 1: Encontrar todos os diretórios "folha" que correspondem ao II desejado
    for root, dirs, files in os.walk(source_path):
        if os.path.basename(root) == folder_to_keep and not dirs:
            # Constrói o novo caminho de destino
            # Ex: De 'results/mesh/4x4/8/II_1' para 'results_new/mesh/4x4/8'
            # (Remove a parte 'II_1' e a base 'results')
            relative_path = os.path.relpath(os.path.dirname(root), source_path)
            destination_dir = os.path.join(dest_path, relative_path)
            tasks.append((root, destination_dir, args.move))

    if not tasks:
        print(f"No directories named '{folder_to_keep}' were found. Nothing to do.")
        return

    operation = "Moving" if args.move else "Copying"
    print(f"Found {len(tasks)} directories to process. Starting parallel {operation.lower()}...")

    total_files = 0
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(copy_directory_contents, src, dest, move) for src, dest, move in tasks]
        for i, future in enumerate(as_completed(futures)):
            print(f"Progress: {i + 1}/{len(tasks)} directories processed.")
            total_files += future.result()
    
    print("\n--- Reorganization Complete ---")
    print(f"Successfully processed a total of {total_files} files.")
    print(f"New organized data is available in: '{dest_path}'")

if __name__ == "__main__":
    main()
