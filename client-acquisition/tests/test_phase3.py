import tempfile
import unittest
from pathlib import Path

from lead_engine.csv_loader import load_leads
from orchestrator.agent_loader import AgentCatalog


ROOT = Path(__file__).resolve().parents[2]


class Phase3FoundationTests(unittest.TestCase):
    def test_catalog_loads_existing_specialists(self):
        catalog = AgentCatalog(ROOT)
        self.assertIn("company_researcher", catalog.mapping)
        self.assertIn("outbound_strategy", catalog.mapping)
        persona = catalog.load("outbound_strategy")
        self.assertIn("Outbound Strategist", persona)
        self.assertIn("signal-based outbound", persona.lower())

    def test_csv_loader_preserves_verified_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "leads.csv"
            path.write_text(
                "company_name,contact_name,website,evidence\n"
                "Acme,Asha,https://acme.test,Shopify storefront\n",
                encoding="utf-8",
            )
            leads = load_leads(path)
            self.assertEqual(len(leads), 1)
            self.assertEqual(leads[0].company_name, "Acme")
            self.assertEqual(leads[0].metadata["evidence"], "Shopify storefront")


if __name__ == "__main__":
    unittest.main()
