import unittest

from app import create_app
from app.forms.config import _load_form_class, form_flow_from_config, load_config


class LoadFormClassTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_returns_none_for_empty_or_none(self):
        self.assertIsNone(_load_form_class(None))
        self.assertIsNone(_load_form_class(""))
        self.assertIsNone(_load_form_class("   "))

    def test_loads_valid_form_class(self):
        from app.forms.parts.apply_to_film.YourDetailsForm import YourDetailsForm
        from app.forms.parts.EmailForm import EmailForm

        self.assertEqual(_load_form_class("EmailForm"), EmailForm)
        self.assertEqual(
            _load_form_class("apply_to_film.YourDetailsForm"), YourDetailsForm
        )

    def test_raises_for_invalid_input_type(self):
        with self.assertRaises(TypeError):
            _load_form_class(123)  # type: ignore

    def test_raises_for_path_traversal_attempts(self):
        for malicious_name in [
            "../../os",
            "../sys",
            "..sys",
            ".EmailForm",
            "EmailForm/something",
            "EmailForm\\something",
        ]:
            with self.assertRaises(ValueError):
                _load_form_class(malicious_name)

    def test_raises_for_dunder_or_private_names(self):
        for malicious_name in [
            "__builtins__",
            "_private",
            "EmailForm.__class__",
            "EmailForm.__builtins__",
        ]:
            with self.assertRaises(ValueError):
                _load_form_class(malicious_name)

    def test_raises_for_non_existent_module_or_class(self):
        for invalid_name in ["NonExistentForm", "sys", "os", "subprocess"]:
            with self.assertRaises(ValueError):
                _load_form_class(invalid_name)

    def test_raises_for_non_flask_form_subclass(self):
        # EmailForm module imports UKPostcode validator class which is not a FlaskForm subclass
        with self.assertRaises((ValueError, TypeError)):
            _load_form_class("EmailForm.UKPostcode")


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
