import ast
from pathlib import Path
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "gh_edge_type_predictor_combined.py"
TREE = ast.parse(SOURCE.read_text(encoding="utf-8"), filename=str(SOURCE))
TARGETS = {"parse_llm_prediction_text", "validate_llm_predictions"}
FUNCTIONS = [
    node for node in TREE.body
    if isinstance(node, ast.FunctionDef) and node.name in TARGETS
]
NAMESPACE = {}
exec(compile(ast.Module(body=FUNCTIONS, type_ignores=[]), str(SOURCE), "exec"), NAMESPACE)
parse_llm_prediction_text = NAMESPACE["parse_llm_prediction_text"]
validate_llm_predictions = NAMESPACE["validate_llm_predictions"]

PROMPT_SOURCE = Path(__file__).resolve().parents[1] / "generate_prompt.py"
PROMPT_TREE = ast.parse(PROMPT_SOURCE.read_text(encoding="utf-8"), filename=str(PROMPT_SOURCE))
PROMPT_CLASSIFY = next(
    node for node in PROMPT_TREE.body
    if isinstance(node, ast.FunctionDef) and node.name == "classify_edges"
)
PROMPT_NAMESPACE = {}
exec(
    compile(ast.Module(body=[PROMPT_CLASSIFY], type_ignores=[]), str(PROMPT_SOURCE), "exec"),
    PROMPT_NAMESPACE,
)
prompt_classify_edges = PROMPT_NAMESPACE["classify_edges"]


class Matrix:
    def __init__(self, rows):
        self.rows = rows
        self.shape = (len(rows), len(rows[0]))

    def __getitem__(self, index):
        row, column = index
        return self.rows[row][column]


class ParseLlmPredictionTextTests(unittest.TestCase):
    def test_parses_and_sorts_valid_rows(self):
        self.assertEqual(
            parse_llm_prediction_text("  3, 5  \n\n1,2\n"),
            [(1, 2), (3, 5)],
        )

    def test_rejects_malformed_nonempty_rows(self):
        cases = (
            ("0,3\nnot a prediction\n", "第 2 行"),
            ("0,3,4\n", "第 1 行"),
            ("0,wall\n", "第 1 行"),
        )
        for content, message in cases:
            with self.subTest(content=content):
                with self.assertRaisesRegex(ValueError, message):
                    parse_llm_prediction_text(content)


class ValidateLlmPredictionsTests(unittest.TestCase):
    def test_requires_exactly_one_valid_prediction_for_each_requested_edge(self):
        self.assertEqual(
            validate_llm_predictions([(4, 5), (1, 2)], [1, 4], 6),
            [(1, 2), (4, 5)],
        )

    def test_rejects_missing_predictions(self):
        with self.assertRaisesRegex(ValueError, "缺少边缘预测"):
            validate_llm_predictions([(1, 2)], [1, 4], 6)

    def test_rejects_duplicate_and_unrequested_edges(self):
        with self.assertRaisesRegex(ValueError, "边缘 ID 重复"):
            validate_llm_predictions([(1, 2), (1, 3)], [1], 4)
        with self.assertRaisesRegex(ValueError, "未请求"):
            validate_llm_predictions([(2, 2)], [1], 4)

    def test_rejects_out_of_range_edge_ids(self):
        for edge_id in (-1, 4):
            with self.subTest(edge_id=edge_id):
                with self.assertRaisesRegex(ValueError, "越界"):
                    validate_llm_predictions([(edge_id, 2)], [edge_id], 4)

    def test_rejects_edge_types_outside_zero_through_five(self):
        for edge_type in (-1, 6):
            with self.subTest(edge_type=edge_type):
                with self.assertRaisesRegex(ValueError, "类型必须是 0-5"):
                    validate_llm_predictions([(1, edge_type)], [1], 4)

    def test_accepts_empty_predictions_when_no_edges_need_prediction(self):
        self.assertEqual(validate_llm_predictions([], [], 0), [])

    def test_prompt_generator_requests_the_same_edges_as_the_consumer(self):
        node_attrs = [
            [10, 10, 0],
            [30, 10, 1],
            [50, 10, 1],
            [70, 10, 2],
            [90, 10, 0],
        ]
        edge_conn = Matrix([[0, 1, 2, 3], [4, 2, 3, 4]])
        layout_matrix = Matrix([[0, 1, 1, 2, 0]])

        requested, automatic = prompt_classify_edges(node_attrs, edge_conn, layout_matrix)

        self.assertEqual(requested, [2, 3])
        self.assertEqual(automatic, [0, 1])


if __name__ == "__main__":
    unittest.main()
