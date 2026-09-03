import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.forms.models import FormFlow
from app.forms.parts.test.AlphaBetaGammaForm import AlphaBetaGammaForm


class FormFlowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.ctx = self.app.test_request_context("/")
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def _build_flow(self, path="unit-test-flow", config_hash="hash-1"):
        flow = FormFlow(path=path, config_hash=config_hash, metadata={"key": "value"})
        start = flow.create_starting_page(
            id="start", name="Start", slug="/", form=AlphaBetaGammaForm
        )
        final = flow.create_final_page(id="final", name="Final", slug="final")
        return flow, start, final

    def test_meta_returns_metadata_value_or_default(self):
        flow, _, _ = self._build_flow()
        self.assertEqual(flow.meta("key"), "value")
        self.assertEqual(flow.meta("missing", "fallback"), "fallback")

    def test_create_page_registers_page_in_pages_dict(self):
        flow, _, _ = self._build_flow()
        middle = flow.create_page(id="middle", name="Middle", slug="middle")
        self.assertIn("middle", flow.pages)
        self.assertIs(flow.get_page_by_id("middle"), middle)

    def test_get_all_pages_returns_all_created_pages(self):
        flow, start, final = self._build_flow()
        self.assertCountEqual(flow.get_all_pages(), [start, final])

    def test_get_page_by_id_supports_aliases(self):
        flow, start, final = self._build_flow()
        self.assertIs(flow.get_page_by_id("startingPage"), start)
        self.assertIs(flow.get_page_by_id("finalPage"), final)

    def test_get_page_by_id_raises_for_missing_page(self):
        flow, _, _ = self._build_flow()
        with self.assertRaises(KeyError):
            flow.get_page_by_id("does-not-exist")

    def test_get_page_by_id_requires_an_id(self):
        flow, _, _ = self._build_flow()
        with self.assertRaises(ValueError):
            flow.get_page_by_id("")

    def test_get_page_by_slug_returns_matching_page(self):
        flow, _, final = self._build_flow()
        self.assertIs(flow.get_page_by_slug("final"), final)
        self.assertIsNone(flow.get_page_by_slug("missing"))

    def test_get_starting_page_raises_if_unset(self):
        flow = FormFlow(path="empty-flow", config_hash="hash")
        with self.assertRaises(ValueError):
            flow.get_starting_page()

    def test_get_final_page_raises_if_unset(self):
        flow = FormFlow(path="empty-flow-2", config_hash="hash")
        with self.assertRaises(ValueError):
            flow.get_final_page()

    def test_get_starting_path_for_root_slug(self):
        flow, _, _ = self._build_flow(path="root-slug-flow")
        self.assertEqual(flow.get_starting_path(), "/root-slug-flow/")

    def test_get_data_returns_saved_data_per_page(self):
        flow, start, _ = self._build_flow(path="data-flow")
        start.save_form_data({"option": "a"})
        self.assertEqual(flow.get_data(), {"start": {"option": "a"}, "final": {}})

    def test_has_complete_path_false_until_requirements_met(self):
        flow, start, final = self._build_flow(path="completion-flow")
        final.require_completion_of(start)
        start.form = start.form_class(data=start.get_saved_form_data())
        self.assertFalse(flow.has_complete_path())

        start.save_form_data({"option": "a"})
        # A fresh FormFlow instance is used to avoid the earliest-incomplete-page cache
        flow2, start2, final2 = self._build_flow(path="completion-flow")
        final2.require_completion_of(start2)
        start2.form = start2.form_class(data=start2.get_saved_form_data())
        self.assertTrue(flow2.has_complete_path())

    def test_reset_clears_session_data(self):
        flow, start, _ = self._build_flow(path="reset-flow")
        start.save_form_data({"option": "a"})
        flow.reset()
        self.assertEqual(start.get_saved_form_data(), {})

    def test_is_completion_handled_false_by_default(self):
        flow, _, _ = self._build_flow(path="no-results-flow")
        self.assertFalse(flow.is_completion_handled())

    def test_handle_completion_raises_if_path_incomplete(self):
        flow, start, final = self._build_flow(path="incomplete-flow")
        final.require_completion_of(start)
        start.form = start.form_class(data=start.get_saved_form_data())
        with self.assertRaises(ValueError):
            flow.handle_completion()

    def test_handle_completion_with_no_result_handlers_configured_succeeds(self):
        flow, _, _ = self._build_flow(path="no-handlers-flow")
        self.assertTrue(flow.handle_completion())
        self.assertEqual(flow.get_completion_results(), [])

    def test_handle_completion_raises_for_unsupported_handler_type(self):
        flow, _, _ = self._build_flow(path="bad-handler-flow")
        flow.result_handlers_config = [{"type": "unknown", "details": {"send": {}}}]
        with self.assertRaises(ValueError):
            flow.handle_completion()

    def test_handle_completion_raises_if_details_missing(self):
        flow, _, _ = self._build_flow(path="missing-details-flow")
        flow.result_handlers_config = [{"type": "email"}]
        with self.assertRaises(ValueError):
            flow.handle_completion()

    def test_handle_completion_records_success_result(self):
        mock_handler_class = MagicMock()
        mock_handler = mock_handler_class.return_value
        mock_handler.send.return_value = True

        flow, _, _ = self._build_flow(path="success-flow")
        flow.result_handlers_config = [
            {"type": "fake", "details": {"init": {}, "process": {}, "send": {}}}
        ]

        with patch.dict(
            "app.forms.models.RESULT_HANDLER_CLASSES", {"fake": mock_handler_class}
        ):
            self.assertTrue(flow.handle_completion())

        self.assertTrue(flow.is_completion_handled())

    def test_handle_completion_records_failure_result(self):
        mock_handler_class = MagicMock()
        mock_handler = mock_handler_class.return_value
        mock_handler.send.return_value = False
        mock_handler.result.return_value = {}

        flow, _, _ = self._build_flow(path="failure-flow")
        flow.result_handlers_config = [
            {"type": "fake", "details": {"init": {}, "process": {}, "send": {}}}
        ]

        with patch.dict(
            "app.forms.models.RESULT_HANDLER_CLASSES", {"fake": mock_handler_class}
        ):
            self.assertFalse(flow.handle_completion())

        self.assertFalse(flow.is_completion_handled())

    def test_handle_completion_handles_exceptions_from_handler(self):
        mock_handler_class = MagicMock(side_effect=Exception("boom"))

        flow, _, _ = self._build_flow(path="exception-flow")
        flow.result_handlers_config = [
            {"type": "fake", "details": {"init": {}, "process": {}, "send": {}}}
        ]

        with patch.dict(
            "app.forms.models.RESULT_HANDLER_CLASSES", {"fake": mock_handler_class}
        ):
            self.assertFalse(flow.handle_completion())
