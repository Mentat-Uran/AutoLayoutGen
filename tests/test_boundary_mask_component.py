import contextlib
import io
import json
import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "0_gh_boundary_mask_generator.py"


def load_component(curve):
    geometry = types.ModuleType("Rhino.Geometry")
    geometry.Point3d = lambda x, y, z: (x, y, z)
    geometry.Plane = types.SimpleNamespace(WorldXY=object())
    geometry.PointContainment = types.SimpleNamespace(Inside=1, Coincident=2, Outside=0)
    rhino = types.ModuleType("Rhino")
    rhino.Geometry = geometry

    with mock.patch.dict(sys.modules, {"Rhino": rhino, "Rhino.Geometry": geometry}):
        with contextlib.redirect_stdout(io.StringIO()):
            return runpy.run_path(str(SCRIPT_PATH), init_globals={"bnd_crv": curve})


class BoundaryMaskComponentTests(unittest.TestCase):
    def test_missing_curve_returns_empty_output_without_geometry_calls(self):
        result = load_component(None)
        self.assertEqual(result["a"], [])
        self.assertNotIn("boundary_mask", result)

    def test_valid_curve_is_sampled_once_per_grid_cell(self):
        class Curve:
            def __init__(self):
                self.calls = 0

            def Contains(self, _point, _plane, _tolerance):
                self.calls += 1
                return 1

        curve = Curve()
        result = load_component(curve)
        self.assertEqual(curve.calls, 100)
        self.assertEqual(result["a"], [[1] * 10 for _ in range(10)])
        self.assertEqual(json.loads(result["boundary_mask_json"]), result["a"])


if __name__ == "__main__":
    unittest.main()
