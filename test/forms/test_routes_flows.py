import re
import unittest
from unittest.mock import MagicMock, patch

from app import create_app


class RequiresRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_single_require_blocks_until_prerequisite_is_complete(self):
        rv = self.client.get("/test/requires/alpha/")
        self.assertEqual(rv.status_code, 302)
        self.assertTrue(rv.location.endswith("/test/requires/"))

        # Submitting the start page redirects to the final page, which itself
        # redirects back to alpha since alpha is still incomplete.
        rv = self.client.post(
            "/test/requires/", data={"option": "a"}, follow_redirects=True
        )
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(rv.request.path.endswith("/test/requires/alpha/"))

        rv = self.client.get("/test/requires/alpha/")
        self.assertEqual(rv.status_code, 200)

    def test_multiple_requires_blocks_until_all_prerequisites_are_complete(self):
        rv = self.client.get("/test/requires/beta/")
        self.assertTrue(rv.location.endswith("/test/requires/"))

        self.client.post("/test/requires/", data={"option": "a"})

        rv = self.client.get("/test/requires/beta/")
        self.assertTrue(rv.location.endswith("/test/requires/alpha/"))

        self.client.post("/test/requires/alpha/", data={"option": "a"})

        rv = self.client.get("/test/requires/beta/")
        self.assertEqual(rv.status_code, 200)


class RequiresAnyRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_requires_any_is_satisfied_by_a_single_prerequisite(self):
        rv = self.client.get("/test/requires-any/alpha/")
        self.assertTrue(rv.location.endswith("/test/requires-any/"))

        self.client.post("/test/requires-any/", data={"option": "a"})

        rv = self.client.get("/test/requires-any/alpha/")
        self.assertEqual(rv.status_code, 200)


class RedirectWhenCompleteRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_redirects_to_page_based_on_when_condition(self):
        rv = self.client.post("/test/redirect-when-complete/", data={"option": "a"})
        self.assertTrue(rv.location.endswith("/test/redirect-when-complete/alpha/"))

        self.client = self.app.test_client()
        rv = self.client.post("/test/redirect-when-complete/", data={"option": "b"})
        self.assertTrue(rv.location.endswith("/test/redirect-when-complete/beta/"))

    def test_redirects_to_an_external_url(self):
        rv = self.client.post("/test/redirect-when-complete/", data={"option": "g"})
        self.assertEqual(rv.location, "https://design-system.nationalarchives.gov.uk/")

    def test_unconditional_rule_on_second_page_reaches_final_page(self):
        self.client.post("/test/redirect-when-complete/", data={"option": "a"})
        rv = self.client.post(
            "/test/redirect-when-complete/alpha/", data={"option": "a"}
        )
        self.assertTrue(rv.location.endswith("/test/redirect-when-complete/beta/"))

        rv = self.client.get("/test/redirect-when-complete/beta/")
        self.assertEqual(rv.status_code, 200)


class EmailCompletionRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.app.config["WTF_CSRF_ENABLED"] = False
        self.client = self.app.test_client()

    def test_completing_the_flow_sends_an_email_via_the_configured_result_handler(
        self,
    ):
        with patch("app.forms.result_handlers.boto3.client") as mock_boto3_client:
            mock_ses = MagicMock()
            mock_ses.send_email.return_value = {"MessageId": "ref-123"}
            mock_boto3_client.return_value = mock_ses

            rv = self.client.post(
                "/test/email-completion/",
                data={"email_address": "person@example.com"},
            )
            self.assertTrue(rv.location.endswith("/test/email-completion/final/"))

            rv = self.client.get("/test/email-completion/final/")
            self.assertEqual(rv.status_code, 200)

            mock_ses.send_email.assert_called_once()
            _, kwargs = mock_ses.send_email.call_args
            self.assertEqual(
                kwargs["Destination"]["ToAddresses"], ["person@example.com"]
            )


class CatalogueIssueInputRenderingTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.client = self.app.test_client()

    def _submit_invalid_record(self, **overrides):
        rv = self.client.get("/catalogue/report-an-issue/")
        self.assertEqual(rv.status_code, 200)
        csrf_token = re.search(
            r'<input[^>]*name="csrf_token"[^>]*value="([^"]+)"', rv.text
        )
        self.assertIsNotNone(csrf_token)

        with self.client.session_transaction() as session:
            session["catalogue/report-an-issue"]["created"] = 1

        data = {
            "record_iaid": "invalid-iaid",
            "error_details-error": "A description of the issue",
            "error_details-expected": "The expected information",
            "csrf_token": csrf_token.group(1),
        }
        data.update(overrides)
        with patch("app.lib.validators.is_iaid_valid", return_value=False):
            return self.client.post("/catalogue/report-an-issue/", data=data)

    def test_xss_input_is_escaped_when_form_is_redisplayed(self):
        payload = "<script>alert(1)</script>"

        rv = self._submit_invalid_record(**{"error_details-error": payload})

        self.assertEqual(rv.status_code, 200)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", rv.text)
        self.assertNotIn(payload, rv.text)

    def test_right_to_left_text_is_preserved_when_form_is_redisplayed(self):
        arabic_text = "مرحبا بالعالم"

        rv = self._submit_invalid_record(**{"error_details-error": arabic_text})

        self.assertEqual(rv.status_code, 200)
        self.assertIn(arabic_text, rv.text)

    def test_unicode_input_is_preserved_when_form_is_redisplayed(self):
        name = "Zoë 李 🧪"

        rv = self._submit_invalid_record(**{"reporter-name": name})

        self.assertEqual(rv.status_code, 200)
        self.assertIn(f'value="{name}"', rv.text)
