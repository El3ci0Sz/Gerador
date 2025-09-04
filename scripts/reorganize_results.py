# scripts/reorganize_results.py

import os
import shutil
import argparse
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def process_directory_task(source_dir: str, dest_dir: str, use_move_operation: bool) -> int:
    """
    Worker function to move or copy all files from a source directory to a new destination directory.
    
    Args:
        source_dir (str): The full path to the source leaf directory (e.g., '.../II_1/').
        dest_dir (str): The full path to the new destination directory.
        use_move_operation (bool): If True, move files; otherwise, copy them.

    Returns:
        int: The number of files successfully processed.
    """
    try:
        if not os.path.isdir(source_dir):
            return 0
            
        os.makedirs(dest_dir, exist_ok=True)
        
        files_processed = 0
        for filename in os.listdir(source_dir):
            source_path = os.path.join(source_dir, filename)
            dest_path = os.path.join(dest_dir, filename)
            
            if os.path.isfile(source_path):
                if use_move_operation:
                    shutil.move(source_path, dest_path)
                else:
                    shutil.copy2(source_path, dest_path)
                files_processed += 1
        
        logging.info(f"Processed {files_processed} files from '{os.path.basename(source_dir)}' to '{dest_dir}'")
        return files_processed
    except Exception as e:
        logging.error(f"Failed to process directory {source_dir}: {e}", exc_info=True)
        return 0

def main():
    """Main function to find directories and orchestrate the reorganization."""
    parser = argparse.ArgumentParser(
        description="Reorganizes a results directory from the old structure (.../NODES/II/) to the new structure (.../II/../NODES/).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("source_dir", help="The root directory with the results in the OLD structure.")
    parser.add_argument("dest_dir", help="The new root directory where the reorganized results will be saved.")
    parser.add_argument("--move", action='store_true', help="Move files instead of copying. This is faster but modifies the source directory.")
    args = parser.parse_args()

    source_path = os.path.abspath(args.source_dir)
    dest_path = os.path.abspath(args.dest_dir)

    if not os.path.isdir(source_path):
        print(f"Error: Source directory '{source_path}' does not exist.")
        return

    if source_path == dest_path:
        print("Error: Source and destination directories cannot be the same.")
        return

    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
        print(f"Destination directory '{dest_path}' created.")

    tasks = []
    print("Scanning source directory to find leaf directories to process...")

    for root, dirs, files in os.walk(source_path):
        # A estrutura antiga tem os arquivos em diretórios que começam com "II_" e não têm subdiretórios
        if os.path.basename(root).startswith("II_") and not dirs:
            try:
                # 1. Parse do caminho antigo
                path_parts = os.path.normpath(root).split(os.sep)
                
                ii_part = path_parts[-1]
                nodes_part = path_parts[-2]
                arch_part = path_parts[-3]
                conn_part = path_parts[-4]
                
                # O "resto" do caminho base antes das partes de configuração
                base_path_parts = path_parts[:-4]
                relative_base = os.path.relpath(os.path.join(*base_path_parts), start=source_path)
                
                # 2. Construção do novo caminho de destino para o DIRETÓRIO
                # A parte 'relative_base' lida com nomes de pastas como 'mappings_cgra_grammar'
                new_dest_dir = os.path.join(dest_path, relative_base, ii_part, conn_part, arch_part, nodes_part)
                
                tasks.append((root, new_dest_dir, args.move))
            except IndexError:
                continue

    if not tasks:
        print("No directories found matching the old structure (.../nodes/II_...). Nothing to do.")
        return

    operation = "Moving" if args.move else "Copying"
    print(f"Found {len(tasks)} directories to process. Starting parallel {operation.lower()}...")

    total_files_processed = 0
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_directory_task, src, dest, move_flag) for src, dest, move_flag in tasks]
        for i, future in enumerate(as_completed(futures)):
            print(f"Progress: {i + 1}/{len(tasks)} directories processed.")
            total_files_processed += future.result()
    
    print("\n--- Reorganization Complete ---")
    print(f"Successfully processed a total of {total_files_processed} files.")
    print(f"New organized data is available in: '{dest_path}'")
    
    if args.move:
        print("Note: The original directory has been modified as files were moved.")

if __name__ == "__main__":
    main()
