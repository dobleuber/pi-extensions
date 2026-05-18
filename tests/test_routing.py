import unittest
from pathlib import Path

from roger.routing.registry import SessionRegistry
from roger.routing.router import RouteDecision, Router


class RoutingTests(unittest.TestCase):
    def test_registry_initializes_system_and_current_project(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project"))

        self.assertEqual(registry.get("system").cwd, Path.home())
        self.assertEqual(registry.get("current-project").cwd, Path("/tmp/project"))

    def test_router_classifies_system_tasks(self):
        router = Router(SessionRegistry.default(project_dir=Path("/tmp/project")))

        for text in [
            "instala steam",
            "actualiza el sistema",
            "mata firefox",
            "desinstala spotify",
            "dame la hora en colombia",
            "que hora es en bogota",
            "dime la fecha de hoy",
        ]:
            with self.subTest(text=text):
                decision = router.route(text)
                self.assertEqual(decision.session_name, "system")
                self.assertFalse(decision.needs_clarification)

    def test_router_keeps_vague_instructions_ambiguous(self):
        router = Router(SessionRegistry.default(project_dir=Path("/tmp/project")))

        decision = router.route("haz eso")

        self.assertTrue(decision.needs_clarification)
        self.assertIsNone(decision.session_name)

    def test_router_classifies_current_project_tasks(self):
        router = Router(SessionRegistry.default(project_dir=Path("/tmp/project")))

        for text in ["corre los tests", "edita el readme", "crea un demo", "inspecciona el codigo"]:
            with self.subTest(text=text):
                decision = router.route(text)
                self.assertEqual(decision.session_name, "current-project")
                self.assertFalse(decision.needs_clarification)

    def test_router_flags_ambiguous_destructive_context(self):
        router = Router(SessionRegistry.default(project_dir=Path("/tmp/project")))

        decision = router.route("borra la carpeta build")

        self.assertTrue(decision.needs_clarification)
        self.assertIsNone(decision.session_name)
        self.assertIn("contexto", decision.question.lower())


if __name__ == "__main__":
    unittest.main()
