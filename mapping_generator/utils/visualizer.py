# mapping_generator/utils/visualizer.py

import os
import logging
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)

class GraphVisualizer:
    """A utility class for exporting graphs to DOT files and rendering images."""

    @staticmethod
    def _write_dot_file(graph: nx.DiGraph, dot_filename: str):
        """Internal helper to write a graph to a .dot file with ranked layout."""
        levels = defaultdict(list)
        try:
            for node in nx.topological_sort(graph):
                level = 0
                for pred in graph.predecessors(node):
                    level = max(level, graph.nodes[pred].get('level', -1) + 1)
                graph.nodes[node]['level'] = level
                levels[level].append(node)
        except nx.NetworkXUnfeasible:
            logger.warning("Graph contains cycles; cannot calculate levels for alignment.")
            levels.clear()

        with open(dot_filename, "w", encoding="utf-8") as f:
            f.write("strict digraph {\n")
            f.write("    rankdir=TB;\n")
            for node, data in graph.nodes(data=True):
                node_name = data.get('name', str(node))
                opcode = data.get('opcode', 'op')
                f.write(f'    "{node_name}" [opcode={opcode}];\n')
            f.write("\n")
            for src, dst in sorted(graph.edges()):
                source_name = graph.nodes[src].get('name', str(src))
                dest_name = graph.nodes[dst].get('name', str(dst))
                f.write(f'    "{source_name}" -> "{dest_name}";\n')
            if levels:
                for level in sorted(levels.keys()):
                    nodes_in_level = " ".join([f'"{graph.nodes[n].get("name", str(n))}"' for n in levels[level]])
                    if len(levels[level]) > 1:
                        f.write(f"    {{ rank = same; {nodes_in_level} }}\n")
            f.write("}\n")

    @staticmethod
    def generate_custom_dot_and_image(graph: nx.DiGraph, dot_filename: str, output_image_filename: str):
        """Generates a .dot file and renders a PNG image from a NetworkX graph."""
        if not graph or not graph.nodes:
            logger.warning("Graph is empty, no image to generate.")
            return
        
        try:
            GraphVisualizer._write_dot_file(graph, dot_filename)
            logger.info(f"Custom .dot file saved to '{dot_filename}'")
        except Exception as e:
            logger.error(f"Error writing custom .dot file: {e}")
            return
        
        try:
            base_name = os.path.splitext(output_image_filename)[0]
            command = f"dot -Tpng {dot_filename} -o {base_name}.png"
            os.system(command)
            logger.info(f"Logical layout image saved to '{base_name}.png'")
        except Exception as e:
           logger.error(f"Error generating image with Graphviz: {e}")

    @staticmethod
    def generate_dot_file_only(graph: nx.DiGraph, dot_filename: str):
        """Generates a .dot file without rendering an image."""
        if not graph or not graph.nodes:
            logger.warning("Graph is empty, no .dot file to generate.")
            return
        
        try:
            GraphVisualizer._write_dot_file(graph, dot_filename)
            logger.info(f"DOT file only saved to '{dot_filename}'")
        except Exception as e:
            logger.error(f"Error writing .dot file: {e}")
