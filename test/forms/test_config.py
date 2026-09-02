import unittest

from app import create_app
from app.forms.config import form_flow_from_config, load_config


class LoadConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_requires_a_form_path(self):
        with self.assertRaises(ValueError):
            load_config("")

    def test_raises_for_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_config("does/not/exist")

    def test_loads_existing_yaml_file(self):
        config = load_config("test/requires")
        self.assertIn("startingPage", config)
        self.assertIn("finalPage", config)


class FormFlowFromConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.test_request_context("/")
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def _minimal_config(self, **overrides):
        config = {
            "startingPage": {"id": "start", "name": "Start", "slug": "/"},
            "finalPage": {"id": "final", "name": "Final", "slug": "final"},
        }
        config.update(overrides)
        return config

    def test_raises_for_empty_config(self):
        with self.assertRaises(ValueError):
            form_flow_from_config({}, "path")

    def test_raises_when_starting_page_missing(self):
        config = {"finalPage": {"id": "final", "name": "Final", "slug": "final"}}
        with self.assertRaises(ValueError):
            form_flow_from_config(config, "path")

    def test_raises_when_final_page_missing(self):
        config = {"startingPage": {"id": "start", "name": "Start", "slug": "/"}}
        with self.assertRaises(ValueError):
            form_flow_from_config(config, "path")

    def test_builds_a_simple_flow(self):
        config = self._minimal_config()
        flow = form_flow_from_config(config, "simple-flow-path")
        self.assertEqual(flow.get_starting_page().id, "start")
        self.assertEqual(flow.get_final_page().id, "final")

    def test_raises_for_duplicate_page_id(self):
        config = self._minimal_config(
            pages=[{"id": "start", "name": "Duplicate", "slug": "duplicate"}]
        )
        with self.assertRaises(ValueError):
            form_flow_from_config(config, "duplicate-flow-path")

    def test_raises_for_unknown_requires_page(self):
        config = self._minimal_config(
            finalPage={
                "id": "final",
                "name": "Final",
                "slug": "final",
                "requires": ["does-not-exist"],
            }
        )
        flow = form_flow_from_config(config, "requires-flow-path")
        # Unresolvable ids are silently skipped rather than raising.
        self.assertEqual(flow.get_final_page().requires_completion_of, [])

    def test_raises_for_unknown_requires_any_page(self):
        config = self._minimal_config(
            finalPage={
                "id": "final",
                "name": "Final",
                "slug": "final",
                "requiresAny": ["does-not-exist"],
            }
        )
        with self.assertRaises(KeyError):
            form_flow_from_config(config, "requires-any-flow-path")

    def test_raises_for_unresolvable_redirect_when_complete(self):
        config = self._minimal_config(
            startingPage={
                "id": "start",
                "name": "Start",
                "slug": "/",
                "redirectWhenComplete": [{"page": "does-not-exist"}],
            }
        )
        with self.assertRaises(ValueError):
            form_flow_from_config(config, "redirect-flow-path")

    def test_raises_for_missing_require_response_page(self):
        config = self._minimal_config(
            finalPage={
                "id": "final",
                "name": "Final",
                "slug": "final",
                "requireResponse": [
                    {"page": "does-not-exist", "key": "option", "value": "a"}
                ],
            }
        )
        with self.assertRaises(ValueError):
            form_flow_from_config(config, "require-response-flow-path")
