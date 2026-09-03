import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.forms.result_handlers import (
    RESULT_HANDLER_CLASSES,
    APIResultHandler,
    EmailResultHandler,
    MicrosoftDynamicsResultHandler,
    MongoDBResultHandler,
    PostgresResultHandler,
    deep_get,
)


class DeepGetTestCase(unittest.TestCase):
    def test_deep_get_returns_nested_value(self):
        data = {"a": {"b": {"c": 1}}}
        self.assertEqual(deep_get(data, "a.b.c"), 1)

    def test_deep_get_returns_default_when_missing(self):
        data = {"a": {}}
        self.assertEqual(deep_get(data, "a.b.c", "fallback"), "fallback")

    def test_deep_get_returns_default_when_not_a_dict(self):
        data = {"a": "not-a-dict"}
        self.assertIsNone(deep_get(data, "a.b"))


class ResultHandlerRegistryTestCase(unittest.TestCase):
    def test_registry_contains_expected_handler_types(self):
        self.assertEqual(
            set(RESULT_HANDLER_CLASSES.keys()),
            {"email", "postgres", "mongodb", "api", "microsoft_dynamics"},
        )
        self.assertIs(RESULT_HANDLER_CLASSES["email"], EmailResultHandler)
        self.assertIs(RESULT_HANDLER_CLASSES["postgres"], PostgresResultHandler)
        self.assertIs(RESULT_HANDLER_CLASSES["mongodb"], MongoDBResultHandler)
        self.assertIs(RESULT_HANDLER_CLASSES["api"], APIResultHandler)
        self.assertIs(
            RESULT_HANDLER_CLASSES["microsoft_dynamics"],
            MicrosoftDynamicsResultHandler,
        )


class PostgresResultHandlerTestCase(unittest.TestCase):
    def test_send_returns_false_and_result_is_empty(self):
        handler = PostgresResultHandler()
        handler.process(data={})
        self.assertFalse(handler.send())
        self.assertEqual(handler.result(), {})


class MongoDBResultHandlerTestCase(unittest.TestCase):
    def test_send_returns_false_and_result_is_empty(self):
        handler = MongoDBResultHandler()
        handler.process(data={})
        self.assertFalse(handler.send())
        self.assertEqual(handler.result(), {})


class APIResultHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_init_requires_url_and_method(self):
        with self.assertRaises(ValueError):
            APIResultHandler()

    def test_send_without_process_raises(self):
        handler = APIResultHandler(url="https://example.com", method="post")
        with self.assertRaises(ValueError):
            handler.send()

    @patch("app.forms.result_handlers.post")
    def test_send_post_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        handler = APIResultHandler(url="https://example.com", method="post")
        handler.process(data={"a": 1})
        self.assertTrue(handler.send())
        mock_post.assert_called_once()

    @patch("app.forms.result_handlers.get")
    def test_send_get_success(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        handler = APIResultHandler(url="https://example.com", method="get")
        handler.process(data={"a": 1})
        self.assertTrue(handler.send())
        mock_get.assert_called_once()

    @patch("app.forms.result_handlers.post")
    def test_send_returns_false_on_non_ok_status(self, mock_post):
        mock_post.return_value = MagicMock(status_code=500)
        handler = APIResultHandler(url="https://example.com", method="post")
        handler.process(data={"a": 1})
        self.assertFalse(handler.send())

    def test_send_raises_for_unsupported_method_is_caught(self):
        handler = APIResultHandler(url="https://example.com", method="delete")
        handler.process(data={"a": 1})
        self.assertFalse(handler.send())

    def test_result_is_always_empty(self):
        handler = APIResultHandler(url="https://example.com", method="post")
        self.assertEqual(handler.result(), {})


class MicrosoftDynamicsResultHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_send_always_returns_false(self):
        handler = MicrosoftDynamicsResultHandler(
            url="https://example.com", method="post"
        )
        handler.process(data={"a": 1})
        self.assertFalse(handler.send())
        self.assertEqual(handler.result(), {})


class EmailResultHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    @patch("app.forms.result_handlers.boto3.client")
    def test_send_without_process_raises(self, mock_boto3_client):
        handler = EmailResultHandler()
        with self.assertRaises(ValueError):
            handler.send()

    @patch("app.forms.result_handlers.boto3.client")
    def test_send_requires_a_recipient(self, mock_boto3_client):
        handler = EmailResultHandler()
        handler.process(data={}, template="outputs/email_json_dump.html")
        with self.assertRaises(ValueError):
            handler.send()

    @patch("app.forms.result_handlers.boto3.client")
    def test_send_success_with_explicit_to_address(self, mock_boto3_client):
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {"MessageId": "msg-123"}
        mock_boto3_client.return_value = mock_ses

        handler = EmailResultHandler()
        handler.process(data={}, template="outputs/email_json_dump.html")
        self.assertTrue(handler.send(to="person@example.com", subject="Hello"))
        self.assertEqual(handler.result(), {"id": "msg-123"})

        _, kwargs = mock_ses.send_email.call_args
        self.assertEqual(kwargs["Destination"]["ToAddresses"], ["person@example.com"])
        self.assertEqual(kwargs["Message"]["Subject"]["Data"], "Hello")

    @patch("app.forms.result_handlers.boto3.client")
    def test_send_resolves_recipient_via_to_var(self, mock_boto3_client):
        mock_ses = MagicMock()
        mock_ses.send_email.return_value = {"MessageId": "msg-456"}
        mock_boto3_client.return_value = mock_ses

        handler = EmailResultHandler()
        handler.process(
            data={"data": {"start": {"email_address": "found@example.com"}}},
            template="outputs/email_json_dump.html",
        )
        self.assertTrue(handler.send(toVar="data.start.email_address"))

        _, kwargs = mock_ses.send_email.call_args
        self.assertEqual(kwargs["Destination"]["ToAddresses"], ["found@example.com"])

    @patch("app.forms.result_handlers.boto3.client")
    def test_send_returns_false_when_ses_raises(self, mock_boto3_client):
        mock_ses = MagicMock()
        mock_ses.send_email.side_effect = Exception("boom")
        mock_boto3_client.return_value = mock_ses

        handler = EmailResultHandler()
        handler.process(data={}, template="outputs/email_json_dump.html")
        self.assertFalse(handler.send(to="person@example.com"))
