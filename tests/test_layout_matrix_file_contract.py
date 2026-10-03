import ast
from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_MATRIX_FILE = "FPGGen_RoomLayoutMatrix_10x10.json"


def read_tree(filename):
    path = REPOSITORY_ROOT / filename
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def read_matrix_file_constants(filename):
    tree = read_tree(filename)
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value.startswith("FPGGen_RoomLayoutMatrix")
        and node.value.endswith(".json")
    }


class LayoutMatrixFileContractTests(unittest.TestCase):
    def test_generator_writes_the_shared_layout_filename(self):
        tree = read_tree("1_gh_room_layout_generator.py")
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        output_names = {
            assignment.value.value
            for assignment in ast.walk(main)
            if isinstance(assignment, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "output_file" for target in assignment.targets)
            and isinstance(assignment.value, ast.Constant)
            and isinstance(assignment.value.value, str)
        }
        self.assertEqual(output_names, {EXPECTED_MATRIX_FILE})

    def test_all_consumers_read_the_shared_layout_filename(self):
        consumers = (
            "2_gh_room_layout_grid_processor.py",
            "generate_prompt.py",
            "gh_edge_type_predictor_combined.py",
        )
        for filename in consumers:
            with self.subTest(filename=filename):
                self.assertEqual(read_matrix_file_constants(filename), {EXPECTED_MATRIX_FILE})


if __name__ == "__main__":
    unittest.main()
