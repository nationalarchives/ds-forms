import unittest
from unittest.mock import MagicMock

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, InputRequired

from app import create_app
from app.forms.models import FormFlow
from app.forms.parts.TestAlphaBetaGammaForm import (
    TestAlphaBetaGammaForm as AlphaBetaGammaForm,
)


class InputRequiredForm(FlaskForm):
    name = StringField("Name", validators=[InputRequired()])


class FormPageTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.ctx = self.app.test_request_context("/")
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def _build_flow(self, path="form-page-flow"):
        flow = FormFlow(path=path, config_hash="hash-1")
        start = flow.create_starting_page(
            id="start", name="Start", slug="/", form=AlphaBetaGammaForm
        )
        final = flow.create_final_page(id="final", name="Final", slug="final")
        return flow, start, final

    def test_input_required_validator_is_rejected(self):
        flow = FormFlow(path="input-required-flow", config_hash="hash-1")
        with self.assertRaises(ValueError):
            flow.create_starting_page(
                id="start", name="Start", slug="/", form=InputRequiredForm
            )

    def test_get_page_path_for_root_slug(self):
        _, start, _ = self._build_flow(path="page-path-root")
        self.assertEqual(start.get_page_path(), "/page-path-root/")

    def test_get_page_path_for_non_root_slug(self):
        _, _, final = self._build_flow(path="page-path-final")
        self.assertEqual(final.get_page_path(), "/page-path-final/final/")

    def test_require_completion_of_is_chainable_and_appends(self):
        _, start, final = self._build_flow(path="require-completion")
        result = final.require_completion_of(start)
        self.assertIs(result, final)
        self.assertEqual(final.requires_completion_of, [start])

    def test_require_completion_of_any_sets_pages_and_fallback(self):
        flow, start, final = self._build_flow(path="require-any")
        other = flow.create_page(id="other", name="Other", slug="other")
        final.require_completion_of_any([start, other], fallback_page=start)
        self.assertEqual(final.requires_completion_of_any, [start, other])
        self.assertIs(final.requires_completion_of_any_fallback, start)

    def test_require_response_appends_a_tuple(self):
        _, start, final = self._build_flow(path="require-response")
        final.require_response(start, "option", "a")
        self.assertEqual(final.requires_responses, [(start, "option", "a")])

    def test_redirect_when_complete_requires_a_target(self):
        _, _, final = self._build_flow(path="redirect-target-required")
        with self.assertRaises(ValueError):
            final.redirect_when_complete()

    def test_redirect_when_complete_appends_a_page_rule(self):
        _, start, final = self._build_flow(path="redirect-page-rule")
        final.redirect_when_complete(page=start)
        self.assertEqual(len(final.when_complete), 1)
        self.assertIs(final.when_complete[0].page, start)

    def test_clear_on_completion_appends_pages(self):
        _, start, final = self._build_flow(path="clear-on-completion")
        result = final.clear_on_completion(start)
        self.assertIs(result, final)
        self.assertEqual(final.clear_pages_on_completion, [start])

    def test_save_and_get_form_data_round_trip(self):
        _, start, _ = self._build_flow(path="save-form-data")
        self.assertEqual(start.get_saved_form_data(), {})
        start.save_form_data({"option": "a"})
        self.assertEqual(start.get_saved_form_data(), {"option": "a"})

    def test_altcha_verified_true_when_altcha_disabled(self):
        _, start, _ = self._build_flow(path="altcha-disabled")
        self.assertTrue(start.altcha_verified())

    def test_altcha_verified_on_get_reads_cached_session_value(self):
        flow = FormFlow(path="altcha-get", config_hash="hash-1")
        start = flow.create_starting_page(
            id="start",
            name="Start",
            slug="/",
            form=AlphaBetaGammaForm,
            altcha=True,
        )
        start.save_form_data({"option": "a"})
        # Session default is True when nothing has been recorded yet.
        self.assertTrue(start.altcha_verified())

    def test_altcha_verified_on_post_delegates_to_verifier(self):
        with self.app.test_request_context(
            "/altcha-post/", method="POST", data={"altcha": "some-payload"}
        ):
            flow = FormFlow(path="altcha-post", config_hash="hash-1")
            start = flow.create_starting_page(
                id="start",
                name="Start",
                slug="/",
                form=AlphaBetaGammaForm,
                altcha=True,
            )
            mock_verifier = MagicMock()
            mock_verifier.verify.return_value = True
            start.altcha_verifier = mock_verifier

            self.assertTrue(start.altcha_verified(save_result=True))
            mock_verifier.verify.assert_called_once_with("some-payload")
            mock_verifier.mark_solved.assert_called_once_with("some-payload")
            self.assertEqual(start.get_saved_form_data().get("altcha"), True)

    def test_altcha_verified_on_post_records_failure(self):
        with self.app.test_request_context(
            "/altcha-post-fail/", method="POST", data={"altcha": "some-payload"}
        ):
            flow = FormFlow(path="altcha-post-fail", config_hash="hash-1")
            start = flow.create_starting_page(
                id="start",
                name="Start",
                slug="/",
                form=AlphaBetaGammaForm,
                altcha=True,
            )
            mock_verifier = MagicMock()
            mock_verifier.verify.return_value = False
            start.altcha_verifier = mock_verifier

            self.assertFalse(start.altcha_verified())
            mock_verifier.mark_solved.assert_not_called()
            self.assertEqual(start.get_saved_form_data().get("altcha"), False)

    def test_is_complete_uses_saved_data_when_no_live_form(self):
        _, start, _ = self._build_flow(path="is-complete")
        self.assertFalse(start.is_complete(temporary_validation=True))
        start.save_form_data({"option": "a"})
        self.assertTrue(start.is_complete(temporary_validation=True))

    def test_is_complete_with_no_form_class_is_always_true(self):
        _, _, final = self._build_flow(path="is-complete-no-form")
        self.assertTrue(final.is_complete(temporary_validation=True))
