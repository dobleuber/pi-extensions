import json
import unittest
from pathlib import Path


EXTENSION_DIR = Path.home() / ".pi" / "agent" / "extensions" / "pi-router"


class PiRouterExtensionStructureTests(unittest.TestCase):
    def test_extension_package_has_installable_pi_entrypoint(self):
        package_path = EXTENSION_DIR / "package.json"
        self.assertTrue(package_path.exists(), "pi-router package.json should exist")

        package = json.loads(package_path.read_text(encoding="utf-8"))

        self.assertEqual(package["name"], "pi-router-extension")
        self.assertEqual(package["type"], "module")
        self.assertEqual(package["pi"]["extensions"], ["./src/index.ts"])
        self.assertIn("test", package["scripts"])

    def test_extension_source_and_docs_are_present(self):
        index_path = EXTENSION_DIR / "src" / "index.ts"
        readme_path = EXTENSION_DIR / "README.md"
        test_path = EXTENSION_DIR / "tests" / "structure.test.ts"

        self.assertTrue(index_path.exists(), "src/index.ts should be the Pi extension entrypoint")
        self.assertTrue(readme_path.exists(), "README.md should explain install/use")
        self.assertTrue(test_path.exists(), "extension should include colocated tests")

        source = index_path.read_text(encoding="utf-8")
        self.assertIn("export default function", source)
        self.assertIn("ExtensionAPI", source)


if __name__ == "__main__":
    unittest.main()
