import unittest

from app.scripts.normalize_provider_keys import _should_run


class NormalizeProviderKeysScriptTests(unittest.TestCase):
    def test_should_run_honors_include(self):
        self.assertTrue(_should_run("providers", ["providers"], []))
        self.assertFalse(_should_run("model_catalog", ["providers"], []))

    def test_should_run_honors_exclude(self):
        self.assertFalse(_should_run("providers", None, ["providers"]))
        self.assertTrue(_should_run("system_configs", None, ["providers"]))


if __name__ == "__main__":
    unittest.main()
