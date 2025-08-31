# scripts/summarize_results.py

import os
import pandas as pd
import argparse
from collections import defaultdict

def summarize_directory(source_dir: str, output_csv: str):
    """Analyzes a directory of results, counts graphs per configuration,
    and saves a summary to a CSV file.

    Args:
        source_dir (str): The root directory containing the generated results.
        output_csv (str): The path for the output CSV file.
    """
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        return

    results = defaultdict(dict)
    
    print(f"Analyzing directories in '{source_dir}'...")

    for root, dirs, files in os.walk(source_dir):
        if not dirs and files:
            try:
                path = os.path.normpath(root)
                parts = path.split(os.sep)
                
                graph_size_str = parts[-1]
                arch_size_str = parts[-2]
                conn_type_str = parts[-3]

                if not graph_size_str.endswith('_nodes'):
                    continue

                graph_size = int(graph_size_str.replace('_nodes', ''))
                graph_count = sum(1 for f in files if f.endswith('.dot'))

                if graph_count > 0:
                    column_name = f"{conn_type_str}_{arch_size_str}"
                    results[graph_size][column_name] = graph_count
            
            except (IndexError, ValueError):
                continue

    if not results:
        print("No valid results found. Check the directory structure.")
        return

    print("Processing data and creating DataFrame...")

    df = pd.DataFrame.from_dict(results, orient='index')

    expected_columns = ['mesh_4x4', 'mesh_8x8', 'all_4x4', 'all_8x8']
    for col in expected_columns:
        if col not in df.columns:
            df[col] = 0
            
    df = df[expected_columns].fillna(0)
    df = df.astype(int)
    df.sort_index(inplace=True)
    df['total'] = df.sum(axis=1)
    df.loc['Grand Total'] = df.sum()
    df.index.name = 'graph_size'

    try:
        df.to_csv(output_csv)
        print(f"\nSummary successfully saved to '{output_csv}'")
        print("\nResult Preview:")
        print(df.to_string())
    except Exception as e:
        print(f"\nError saving CSV file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generates a CSV summary of generated graphs per configuration."
    )
    parser.add_argument(
        "source_dir", 
        help="The root directory with the generated results (e.g., mappings_cgra_grammar)."
    )
    parser.add_argument(
        "-o", "--output", 
        default="summary.csv", 
        help="The name for the output CSV file (default: summary.csv)."
    )
    args = parser.parse_args()

    summarize_directory(args.source_dir, args.output)
