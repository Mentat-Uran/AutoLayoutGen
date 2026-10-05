import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "1_gh_room_layout_generator.py"


def load_generator_module():
    sdk_stub = types.ModuleType("volcenginesdkarkruntime")
    sdk_stub.Ark = mock.Mock(name="Ark")
    spec = importlib.util.spec_from_file_location("room_layout_output_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"volcenginesdkarkruntime": sdk_stub}):
        spec.loader.exec_module(module)
    return module


class RoomLayoutOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_generator_module()

    def test_saves_to_current_directory_without_creating_empty_parent(self):
        matrix = [[1, 2], [3, 4]]
        previous_directory = Path.cwd()
        with tempfile.TemporaryDirectory() as temporary_directory:
            try:
                os.chdir(temporary_directory)
                self.module.save_room_layout(matrix, "layout.json")
                self.assertEqual(json.loads(Path("layout.json").read_text()), matrix)
            finally:
                os.chdir(previous_directory)

    def test_creates_a_requested_nested_parent_directory(self):
        matrix = [[1, 0], [0, 1]]
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "nested" / "layout.json"
            self.module.save_room_layout(matrix, output)
            self.assertEqual(json.loads(output.read_text()), matrix)


if __name__ == "__main__":
    unittest.main()
