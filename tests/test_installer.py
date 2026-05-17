import tempfile
import unittest
from pathlib import Path

from roger.installer import AutostartInstaller


class AutostartInstallerTests(unittest.TestCase):
    def test_install_adds_roger_daemon_to_hypr_autostart_lua(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autostart = root / ".config" / "hypr" / "autostart.lua"
            autostart.parent.mkdir(parents=True)
            autostart.write_text('-- Extra autostart processes.\n', encoding="utf-8")
            project = root / "project"
            project.mkdir()

            result = AutostartInstaller(home=root, project_dir=project).install()

            text = autostart.read_text(encoding="utf-8")
            self.assertTrue(result.changed)
            self.assertIn("Roger voice daemon", text)
            self.assertIn("o.exec_on_start", text)
            self.assertIn(f"cd {project}", text)
            self.assertIn("uv run roger daemon", text)
            self.assertTrue(result.backup_path.exists())

    def test_install_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autostart = root / ".config" / "hypr" / "autostart.lua"
            autostart.parent.mkdir(parents=True)
            autostart.write_text('-- Extra autostart processes.\n', encoding="utf-8")
            project = root / "project"
            project.mkdir()
            installer = AutostartInstaller(home=root, project_dir=project)

            first = installer.install()
            second = installer.install()

            text = autostart.read_text(encoding="utf-8")
            self.assertTrue(first.changed)
            self.assertFalse(second.changed)
            self.assertEqual(text.count("Roger voice daemon"), 1)

    def test_uninstall_removes_managed_block_and_keeps_other_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            autostart = root / ".config" / "hypr" / "autostart.lua"
            autostart.parent.mkdir(parents=True)
            autostart.write_text('o.exec_on_start("keep-me")\n', encoding="utf-8")
            project = root / "project"
            project.mkdir()
            installer = AutostartInstaller(home=root, project_dir=project)
            installer.install()

            result = installer.uninstall()

            text = autostart.read_text(encoding="utf-8")
            self.assertTrue(result.changed)
            self.assertIn('o.exec_on_start("keep-me")', text)
            self.assertNotIn("Roger voice daemon", text)


if __name__ == "__main__":
    unittest.main()
