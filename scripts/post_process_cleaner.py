# scripts/post_process_cleaner.py

import os
import shutil
import argparse
import networkx as nx
import logging
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

def load_graph_from_dot(file_path: str) -> nx.DiGraph | None:
    """Safely loads a graph from a .dot file."""
    try:
        return nx.drawing.nx_pydot.read_dot(file_path)
    except Exception:
        return None

def process_and_copy_unique_files(source_dir: str, dest_dir: str) -> int:
    """Worker to process a directory, find unique graphs, and copy their files."""
    logging.info(f"Processing directory: {os.path.basename(source_dir)}")
    dot_files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if f.endswith('.dot')]
    if len(dot_files) < 1: return 0

    groups = defaultdict(list)
    for file_path in dot_files:
        graph = load_graph_from_dot(file_path)
        if graph:
            key = (graph.number_of_nodes(), graph.number_of_edges())
            groups[key].append((file_path, graph))

    unique_files_to_copy = []
    for items in groups.values():
        unique_graphs_in_group = []
        for file_path, graph in items:
            is_isomorphic = any(nx.algorithms.isomorphism.GraphMatcher(graph, ug).is_isomorphic() for _, ug in unique_graphs_in_group)
            if not is_isomorphic:
                unique_graphs_in_group.append((file_path, graph))
                unique_files_to_copy.append(file_path)

    if not unique_files_to_copy: return 0
        
    os.makedirs(dest_dir, exist_ok=True)
    for file_path in unique_files_to_copy:
        base_name = os.path.splitext(file_path)[0]
        try:
            shutil.copy2(f"{base_name}.dot", dest_dir)
            shutil.copy2(f"{base_name}.json", dest_dir)
        except FileNotFoundError:
            logging.warning(f"JSON file for {base_name}.dot not found.")
        except Exception as e:
            logging.error(f"Error copying files for {base_name}: {e}")

    logging.info(f"Directory '{os.path.basename(dest_dir)}' finished. Copied {len(unique_files_to_copy)} unique graphs.")
    return len(unique_files_to_copy)

def run_cleaning_process(source_dir: str, dest_dir: str):
    """Orchestrates the cleaning and copying process."""
    source_path = os.path.abspath(source_dir)
    dest_path = os.path.abspath(dest_dir)

    if not os.path.isdir(source_path):
        print(f"Error: Source directory '{source_path}' does not exist.")
        return

    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
        print(f"Destination directory '{dest_path}' created.")

    tasks = []
    for root, dirs, files in os.walk(source_path):
        if not dirs and any(f.endswith('.dot') for f in files):
            relative_path = os.path.relpath(root, source_path)
            destination_leaf_dir = os.path.join(dest_path, relative_path)
            tasks.append((root, destination_leaf_dir))

    if not tasks:
        print("No directories with .dot files were found to process.")
        return

    print(f"Found {len(tasks)} directories to clean. Starting parallel processing...")
    
    total_unique_graphs = 0
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        futures = [executor.submit(process_and_copy_unique_files, src, dest) for src, dest in tasks]
        for future in as_completed(futures):
            try:
                total_unique_graphs += future.result()
            except Exception as e:
                logging.error(f"A processing task raised an error: {e}", exc_info=True)

    print("\n--- Cleaning Process Complete ---")
    print(f"Total of {total_unique_graphs} unique graphs copied to '{dest_path}'.")

def main():
    """Main function to handle command-line execution."""
    parser = argparse.ArgumentParser(description="Cleans a result directory by keeping only non-isomorphic graphs.")
    parser.add_argument("source_dir", help="The root directory with the generated results.")
    parser.add_argument("dest_dir", help="The new directory where cleaned results will be saved.")
    args = parser.parse_args()
    run_cleaning_process(args.source_dir, args.dest_dir)

if __name__ == "__main__":
    main()
