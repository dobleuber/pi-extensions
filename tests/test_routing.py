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
        self.assertIn("destructive", decision.reason)

    def test_router_explains_keyword_rule_match(self):
        router = Router(SessionRegistry.default(project_dir=Path("/tmp/project")))

        decision = router.route("corre los tests")

        self.assertEqual(decision.session_name, "current-project")
        self.assertEqual(decision.matched_rule, "keyword:tests")
        self.assertIn("current-project", decision.reason)

    def test_registry_can_add_named_project_domain_with_rules(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project")).with_entry(
            "notes",
            cwd=Path("/tmp/notes"),
            description="Personal notes",
            routing_keywords=["nota", "notas"],
        )
        router = Router(registry)

        decision = router.route("abre mis notas")

        self.assertEqual(decision.session_name, "notes")
        self.assertEqual(registry.get("notes").cwd, Path("/tmp/notes"))
        self.assertEqual(decision.matched_rule, "keyword:notas")

    def test_registry_can_add_non_project_domain_without_voice_pipeline_changes(self):
        registry = SessionRegistry.default(project_dir=Path("/tmp/project")).with_entry(
            "media",
            cwd=Path.home(),
            description="Media controls",
            routing_keywords=["musica", "volumen"],
        )

        decision = Router(registry).route("sube el volumen")

        self.assertEqual(decision.session_name, "media")

    def test_safe_ambiguous_default_records_low_confidence(self):
        router = Router(SessionRegistry.default(project_dir=Path("/tmp/project")))

        decision = router.route("revisa esto")

        self.assertTrue(decision.needs_clarification)
        self.assertEqual(decision.confidence, "low")
        self.assertIn("ambiguous", decision.reason)

    def test_registry_validation_reports_malformed_route_rules(self):
        registry = SessionRegistry({
            "bad": SessionRegistry.default(Path("/tmp/project")).get("system").with_updates(
                name="bad",
                routing_keywords="not-a-list",
            )
        })

        errors = registry.validate()

        self.assertTrue(errors)
        self.assertIn("bad", errors[0])


if __name__ == "__main__":
    unittest.main()
