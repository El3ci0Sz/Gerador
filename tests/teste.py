from src.cgra.interconnection import Interconnection
from src.utils.Mapping import Mapping

def print_visual_placement(mapping, dims):
    print("\nVisualização da CGRA (linha x coluna):")
    grid = [["." for _ in range(dims[1])] for _ in range(dims[0])]
    for node, (r, c, _) in mapping.placement.items():
        grid[r][c] = str(node)
    for i, row in enumerate(grid):
        print(f"{i}: {' '.join(row)}")


def run_test(interconnection_type, label):
    print(f"\n{'=' * 10} TESTE: {label} ({interconnection_type}) {'=' * 10}")

    mapping = Mapping(3)
    mapping.placement = {
            0: (0, 3, 0),  # meio
            1: (1, 2, 0),  # canto superior esquerdo
            2: (3, 1, 0),  # canto inferior direito
        }
    cgra_dim = (4, 4)  # 4 linhas, 4 colunas
    II = 2  # Intervalo de Initiation

    ic = Interconnection(cgra_dim, interconnection_type, mapping, II)

    print_visual_placement(mapping, cgra_dim)

    for node in mapping.placement:
        neighbors = ic.neighbor_dict[node]
        print(f"Nó {node} ({mapping.placement[node]}):")
        for neighbor in sorted(neighbors):
            print(f"  → {neighbor}")


if __name__ == "__main__":
    run_test("1000", "MESH")
    run_test("0100", "DIAGONAL")
    run_test("0010", "ONE-HOP")
    run_test("0001", "TOROIDAL")
    run_test("1001", "MESH + TOROIDAL")
    run_test("1100", "MESH + DIAGONAL")
    run_test("1111", "TUDO")

