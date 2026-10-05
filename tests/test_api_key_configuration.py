import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "1_gh_room_layout_generator.py"


def load_generator_module():
    sdk_stub = types.ModuleType("volcenginesdkarkruntime")
    sdk_stub.Ark = mock.Mock(name="Ark")
    spec = importlib.util.spec_from_file_location("room_layout_generator_under_test", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"volcenginesdkarkruntime": sdk_stub}):
        spec.loader.exec_module(module)
    return module, sdk_stub.Ark


class ApiKeyConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module, cls.ark_client = load_generator_module()

    def test_returns_configured_key_from_environment_mapping(self):
        self.assertEqual(
            self.module.require_api_key({"ARK_API_KEY": " local-test-key "}),
            "local-test-key",
        )

    def test_rejects_missing_or_blank_key(self):
        for environment in ({}, {"ARK_API_KEY": ""}, {"ARK_API_KEY": "   "}):
            with self.subTest(environment=environment):
                with self.assertRaisesRegex(RuntimeError, "ARK_API_KEY"):
                    self.module.require_api_key(environment)

    def test_main_fails_before_constructing_client_when_key_is_missing(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "ARK_API_KEY"):
                self.module.main()
        self.ark_client.assert_not_called()


if __name__ == "__main__":
    unittest.main()
