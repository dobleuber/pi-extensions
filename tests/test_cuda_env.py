import unittest
from pathlib import Path

from roger.cuda_env import build_cuda_library_path, command_uses_cuda_stt, find_cuda_library_dirs


class CudaEnvTests(unittest.TestCase):
    def test_command_uses_cuda_stt_for_voice_commands(self):
        self.assertTrue(command_uses_cuda_stt(["roger", "daemon"]))
        self.assertTrue(command_uses_cuda_stt(["roger", "listen-once"]))
        self.assertFalse(command_uses_cuda_stt(["roger", "health"]))

    def test_find_cuda_library_dirs_discovers_dirs_with_cublas12(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib = root / "opt" / "resolve" / "libs"
            lib.mkdir(parents=True)
            (lib / "libcublas.so.12").write_text("", encoding="utf-8")

            dirs = find_cuda_library_dirs(search_roots=[root])

        self.assertEqual(dirs, [lib])

    def test_build_cuda_library_path_prepends_discovered_dirs(self):
        first = Path("/cuda")
        existing = "/usr/lib"

        path = build_cuda_library_path([first], existing)

        self.assertEqual(path, f"{first}:/usr/lib")


if __name__ == "__main__":
    unittest.main()
