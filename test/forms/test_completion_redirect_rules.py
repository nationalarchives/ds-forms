import unittest
from unittest.mock import MagicMock

from app import create_app
from app.forms.models import (
    CompletionRedirectRule,
    FlaskMethodRedirectRule,
    PageRedirectRule,
    URLRedirectRule,
)


class CompletionRedirectRuleTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.test_request_context("/")
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_base_resolve_is_not_implemented(self):
        rule = CompletionRedirectRule()
        with self.assertRaises(NotImplementedError):
            rule.resolve()

    def test_matches_with_no_when_or_condition_always_matches(self):
        rule = CompletionRedirectRule()
        self.assertTrue(rule.matches({}))
        self.assertTrue(rule.matches({"anything": "value"}))

    def test_matches_with_when_tuple(self):
        rule = CompletionRedirectRule(when=("option", "a"))
        self.assertTrue(rule.matches({"option": "a"}))
        self.assertFalse(rule.matches({"option": "b"}))
        self.assertFalse(rule.matches({}))


class PageRedirectRuleTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.test_request_context("/")
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_resolve_returns_the_page_path(self):
        page = MagicMock()
        page.get_page_path.return_value = "/some/page/"
        rule = PageRedirectRule(page=page)
        self.assertEqual(rule.resolve(), "/some/page/")


class FlaskMethodRedirectRuleTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.test_request_context("/")
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_resolve_returns_the_url_for_the_flask_method(self):
        rule = FlaskMethodRedirectRule(flask_method="main.index")
        self.assertEqual(rule.resolve(), "/")


class URLRedirectRuleTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test")
        self.ctx = self.app.test_request_context("/")
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()

    def test_resolve_returns_the_configured_url(self):
        rule = URLRedirectRule(url="https://design-system.nationalarchives.gov.uk/")
        self.assertEqual(
            rule.resolve(), "https://design-system.nationalarchives.gov.uk/"
        )
