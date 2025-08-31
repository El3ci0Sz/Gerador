# Mapping Generator for CGRA and QCA

This project provides tools to generate, process, and analyze DFG (Data Flow Graph) mappings for CGRA and QCA architectures.

## Project Structure

- `mapping_generator/`: The main Python package containing all the core logic.
  - `architectures/`: Defines the CGRA and QCA architecture connectivity.
  - `generation/`: Contains the grammar-based and random mapping generation logic.
  - `utils/`: Helper modules for visualization and graph processing.
- `scripts/`: Executable scripts for running tasks.
  - `runner.py`: The main entry point for running single or campaign generations.
  - `post_process_cleaner.py`: A utility to clean an output directory by keeping only non-isomorphic graphs.
  - `summarize_results.py`: A utility to create a CSV summary of a generation campaign.
- `tests/`: Unit tests for the project.

## Setup

1.  Clone the repository.
2.  It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  You also need to have Graphviz installed on your system for image generation.
    - **Ubuntu/Debian:** `sudo apt-get install graphviz`
    - **macOS (with Homebrew):** `brew install graphviz`

## Usage

The main script for all operations is `scripts/runner.py`. It has two main modes: `single` and `campaign`.

### Single Generation

To run a single, specific generation task with custom parameters:

```bash
python scripts/runner.py single --tec cgra --gen-mode grammar --arch-size 4 4 --graph-range 8 8 --difficulty 5
