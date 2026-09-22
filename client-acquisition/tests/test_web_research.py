import unittest
from unittest.mock import patch

from lead_engine.web_research import (
    _clean_ddg_url,
    _filter_relevant_results,
    _parse_bing_rss,
    _parse_search_html,
    build_queries,
    search_public_web,
)


class WebResearchTests(unittest.TestCase):
    def test_build_queries_contains_company_and_contact(self):
        queries = build_queries("Hyppy", "Sawni Gupta")
        self.assertTrue(any('"Hyppy" ecommerce operations' in q for q in queries))
        self.assertIn('"Sawni Gupta" "Hyppy"', queries)

    def test_clean_ddg_redirect(self):
        url = "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fcareers"
        self.assertEqual(_clean_ddg_url(url), "https://example.com/careers")

    def test_parse_standard_ddg_markup(self):
        html = """
        <a class="result__a" href="https://example.com/careers">Example Careers</a>
        <div class="result__snippet">Hiring ecommerce operations staff.</div>
        """
        results = _parse_search_html(html, max_results=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Example Careers")
        self.assertEqual(results[0].url, "https://example.com/careers")
        self.assertIn("ecommerce operations", results[0].snippet)

    def test_parse_lite_ddg_markup(self):
        html = """
        <a class="result-link" href="https://example.com/shop">Example Shop</a>
        <td class="result-snippet">Shopify store information.</td>
        """
        results = _parse_search_html(html, max_results=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, "https://example.com/shop")
        self.assertIn("Shopify", results[0].snippet)

    def test_parse_bing_rss_markup(self):
        xml = """
        <rss><channel>
          <item><title>Hyppy Home Decor</title><link>https://hyppy.in/</link>
          <description>Hyppy ecommerce store.</description></item>
        </channel></rss>
        """
        results = _parse_bing_rss(xml, max_results=5)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].provider, "bing_rss")
        self.assertEqual(results[0].url, "https://hyppy.in/")

    def test_irrelevant_results_are_filtered(self):
        results = [
            type("Result", (), {"title": "Hyppy Home Decor", "url": "https://hyppy.in/", "snippet": "Hyppy store"})(),
            type("Result", (), {"title": "Google Maps", "url": "https://maps.google.com/maps/search/", "snippet": "Google Maps"})(),
            type("Result", (), {"title": "Generic Careers", "url": "https://example.com/careers", "snippet": "Careers"})(),
        ]
        filtered = _filter_relevant_results(results, '"Hyppy" ecommerce operations', max_results=5)
        self.assertEqual([item.url for item in filtered], ["https://hyppy.in/"])

    @patch("lead_engine.web_research._fetch_search_endpoint")
    def test_search_falls_back_when_first_endpoint_has_no_results(self, mock_fetch):
        mock_fetch.side_effect = [
            [],
            [
                type("Result", (), {
                    "title": "Hyppy Fallback",
                    "url": "https://hyppy.in/fallback",
                    "snippet": "Hyppy fallback result",
                })()
            ],
        ]
        results = search_public_web("Hyppy ecommerce", max_results=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].url, "https://hyppy.in/fallback")
        self.assertEqual(mock_fetch.call_count, 2)
        self.assertEqual(results[0].provider, "duckduckgo_html")


if __name__ == "__main__":
    unittest.main()
