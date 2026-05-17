import tempfile
import unittest
from pathlib import Path

from roger import cli


class CliInstallerTests(unittest.TestCase):
    def test_install_autostart_command_installs_hyprland_autostart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            home = root / "home"

            exit_code, output = cli.run([
                "install-autostart",
                "--home",
                str(home),
                "--project-dir",
                str(project),
            ])

            self.assertEqual(exit_code, 0)
            self.assertIn("installed", output)
            self.assertTrue((home / ".config" / "hypr" / "autostart.lua").exists())

    def test_uninstall_autostart_command_removes_hyprland_autostart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()
            home = root / "home"
            cli.run(["install-autostart", "--home", str(home), "--project-dir", str(project)])

            exit_code, output = cli.run(["uninstall-autostart", "--home", str(home), "--project-dir", str(project)])

            self.assertEqual(exit_code, 0)
            self.assertIn("uninstalled", output)
            self.assertNotIn("Roger voice daemon", (home / ".config" / "hypr" / "autostart.lua").read_text())


if __name__ == "__main__":
    unittest.main()
