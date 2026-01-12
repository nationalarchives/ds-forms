import unittest

from app import create_app


class SitemapBlueprintTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app("config.Test").test_client()
        self.domain = "https://localhost"

    def test_sitemap(self):
        rv = self.app.get("/forms/sitemap.xml")
        self.assertEqual(rv.status_code, 200)
        self.assertIn(
            f"<loc>{self.domain}/apply-to-film-at-the-national-archives/</loc>", rv.text
        )
        self.assertNotIn(f"<loc>{self.domain}/example-form/</loc>", rv.text)
