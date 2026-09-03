import unittest
from unittest.mock import patch

from app import create_app
from app.forms.models import AltchaVerifier


class AltchaVerifierTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.verifier = AltchaVerifier()

    def tearDown(self):
        self.ctx.pop()

    def test_empty_payload_is_not_verified(self):
        self.assertFalse(self.verifier.verify(""))

    @patch("app.forms.models.cache")
    def test_previously_solved_payload_is_rejected(self, mock_cache):
        mock_cache.get.return_value = ["already-solved"]
        self.assertFalse(self.verifier.verify("already-solved"))

    @patch("app.forms.models.verify_solution")
    @patch("app.forms.models.cache")
    def test_valid_payload_is_verified(self, mock_cache, mock_verify_solution):
        mock_cache.get.return_value = []
        mock_verify_solution.return_value = (True, None)
        self.assertTrue(self.verifier.verify("valid-payload"))

    @patch("app.forms.models.verify_solution")
    @patch("app.forms.models.cache")
    def test_invalid_payload_is_rejected(self, mock_cache, mock_verify_solution):
        mock_cache.get.return_value = []
        mock_verify_solution.return_value = (False, None)
        self.assertFalse(self.verifier.verify("invalid-payload"))

    @patch("app.forms.models.verify_solution")
    @patch("app.forms.models.cache")
    def test_verification_error_is_treated_as_unverified(
        self, mock_cache, mock_verify_solution
    ):
        mock_cache.get.return_value = []
        mock_verify_solution.side_effect = Exception("boom")
        self.assertFalse(self.verifier.verify("error-payload"))

    @patch("app.forms.models.cache")
    def test_mark_solved_appends_to_the_cached_list(self, mock_cache):
        mock_cache.get.return_value = ["existing-payload"]
        self.verifier.mark_solved("new-payload")
        mock_cache.set.assert_called_once_with(
            "solved_altchas", ["existing-payload", "new-payload"]
        )

    @patch("app.forms.models.cache")
    def test_mark_solved_with_no_existing_cache(self, mock_cache):
        mock_cache.get.return_value = None
        self.verifier.mark_solved("first-payload")
        mock_cache.set.assert_called_once_with("solved_altchas", ["first-payload"])

    def test_uses_a_custom_hmac_key_config(self):
        verifier = AltchaVerifier(hmac_key_config="SOME_OTHER_KEY")
        self.assertEqual(verifier.hmac_key_config, "SOME_OTHER_KEY")
