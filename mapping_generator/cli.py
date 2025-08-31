# mapping_generator/cli.py

import argparse

def create_parser():
    """Creates and configures the command-line argument parser for the entire application.

    This function defines the main commands ('single', 'campaign') and all their
    respective arguments and options.

    Returns:
        argparse.ArgumentParser: The fully configured parser object.
    """
    parser = argparse.ArgumentParser(
        description="Mapping Generator for CGRA and QCA.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', required=True, help='Available commands')

    parser_single = subparsers.add_parser('single', help='Run a single, specific generation task.')
    parser_single.add_argument('--tec', type=str, default='cgra', choices=['cgra', 'qca'], help='Target technology.')
    parser_single.add_argument('--gen-mode', type=str, default='grammar', choices=['grammar', 'random'], help='Generation mode.')
    parser_single.add_argument('--k-graphs', type=int, default=10, help='Number of graphs to generate.')
    parser_single.add_argument('--difficulty', type=int, default=1, help='Difficulty level for grammar-based generation.')
    parser_single.add_argument('--arch-size', type=int, nargs=2, default=[4, 4], help='Architecture dimensions (rows cols).')
    parser_single.add_argument('--graph-range', type=int, nargs=2, default=[8, 10], help='Min and max number of nodes for the DFG.')
    parser_single.add_argument('--bits', type=str, default='1000', help='CGRA interconnection bits (mesh, diag, hop, tor).')
    parser_single.add_argument('--k-range', type=int, nargs=2, default=[2, 3], help='K-range for grammar rules.')
    parser_single.add_argument('--max-path-length', type=int, default=15, help='Max path length for routing.')
    parser_single.add_argument('--qca-arch', type=str, default='U', choices=['U', 'R', 'T'], help='QCA architecture type.')
    parser_single.add_argument('--no-extend-io', action='store_true', help='Disable I/O extension to border.')
    parser_single.add_argument('--no-images', action='store_true', help='Disable PNG image generation.')
    parser_single.add_argument('--ii', type=int, default=None, help='Specify a fixed Initiation Interval (II). If not set, it will be calculated automatically.')
    parser_single.add_argument('--output-dir', type=str, default='results', help='Base directory to save the output files.')
    parser_single.add_argument('--alpha', type=float, default=0.3, help='For random mode: probability of adding extra edges.')
    parser_single.add_argument('--retries-multiplier', type=int, default=150, help='For grammar mode: multiplier for the max total attempts (k * multiplier).')
    parser_single.set_defaults(func_name='run_single')

    # --- Subcommand for a CAMPAIGN run ---
    parser_campaign = subparsers.add_parser('campaign', help='Run the full, parallel generation campaign.')
    parser_campaign.add_argument('--no-images', action='store_true', help='If specified, disables PNG image generation.')
    parser_campaign.add_argument('-v', '--verbose', action='store_true', help='Show detailed logs from the generation process.')
    parser_campaign.add_argument('--output-dir', type=str, default='results_campaign', help='Base directory to save the campaign output files.')
    parser_campaign.add_argument('--clean', action='store_true', help='Automatically run the post-process cleaner to remove isomorphic graphs after the campaign.')
    parser_campaign.set_defaults(func_name='run_campaign')

    return parser
