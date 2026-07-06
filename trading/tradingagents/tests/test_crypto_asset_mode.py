import unittest

from cli.models import AnalystType, AssetType
from cli.utils import detect_asset_type, filter_analysts_for_asset_type
from tradingagents.graph.propagation import Propagator


class CryptoAssetModeTests(unittest.TestCase):
    def test_detects_crypto_pair_symbols(self):
        self.assertEqual(detect_asset_type("BTC-USD"), AssetType.CRYPTO)
        self.assertEqual(detect_asset_type("eth-usd"), AssetType.CRYPTO)

    def test_defaults_non_crypto_symbols_to_stock(self):
        self.assertEqual(detect_asset_type("AAPL"), AssetType.STOCK)
        self.assertEqual(detect_asset_type("SPY"), AssetType.STOCK)

    def test_filters_out_fundamentals_analyst_for_crypto(self):
        analysts = [
            AnalystType.MARKET,
            AnalystType.SOCIAL,
            AnalystType.NEWS,
            AnalystType.FUNDAMENTALS,
        ]

        self.assertEqual(
            filter_analysts_for_asset_type(analysts, AssetType.CRYPTO),
            [
                AnalystType.MARKET,
                AnalystType.SOCIAL,
                AnalystType.NEWS,
            ],
        )

    def test_keeps_all_analysts_for_stock(self):
        analysts = [
            AnalystType.MARKET,
            AnalystType.SOCIAL,
            AnalystType.NEWS,
            AnalystType.FUNDAMENTALS,
        ]

        self.assertEqual(
            filter_analysts_for_asset_type(analysts, AssetType.STOCK),
            analysts,
        )

    def test_propagator_includes_asset_type_in_initial_state(self):
        state = Propagator().create_initial_state(
            "BTC-USD", "2026-04-18", asset_type=AssetType.CRYPTO.value
        )

        self.assertEqual(state["asset_type"], AssetType.CRYPTO.value)


if __name__ == "__main__":
    unittest.main()
