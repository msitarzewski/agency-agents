"""Tests for symbol normalization and the no-data routing sentinel."""

import unittest

import pytest

from tradingagents.dataflows.symbol_utils import (
    NoMarketDataError,
    is_yahoo_safe,
    normalize_symbol,
)


@pytest.mark.unit
class TestNormalizeSymbol(unittest.TestCase):
    def test_plain_equities_unchanged(self):
        for sym in ("AAPL", "MSFT", "TSM", "BRK.B", "0700.HK", "^GSPC", "GC=F"):
            self.assertEqual(normalize_symbol(sym), sym)

    def test_lowercases_are_upper(self):
        self.assertEqual(normalize_symbol("aapl"), "AAPL")
        self.assertEqual(normalize_symbol("  msft  "), "MSFT")

    def test_metal_aliases_map_to_futures(self):
        self.assertEqual(normalize_symbol("XAUUSD"), "GC=F")
        self.assertEqual(normalize_symbol("XAUUSD+"), "GC=F")   # broker CFD suffix
        self.assertEqual(normalize_symbol("xauusd+"), "GC=F")
        self.assertEqual(normalize_symbol("GOLD"), "GC=F")
        self.assertEqual(normalize_symbol("XAGUSD"), "SI=F")

    def test_energy_and_index_aliases(self):
        self.assertEqual(normalize_symbol("USOIL"), "CL=F")
        self.assertEqual(normalize_symbol("SPX500"), "^GSPC")
        self.assertEqual(normalize_symbol("NAS100"), "^NDX")
        self.assertEqual(normalize_symbol("US30"), "^DJI")

    def test_forex_pairs_get_x_suffix(self):
        self.assertEqual(normalize_symbol("EURUSD"), "EURUSD=X")
        self.assertEqual(normalize_symbol("GBPJPY"), "GBPJPY=X")
        self.assertEqual(normalize_symbol("eurusd"), "EURUSD=X")

    def test_crypto_pairs_get_dash_usd(self):
        self.assertEqual(normalize_symbol("BTCUSD"), "BTC-USD")
        self.assertEqual(normalize_symbol("ETHUSD"), "ETH-USD")

    def test_six_letter_non_currency_left_alone(self):
        # GOOGLE-style 6-letter tickers that aren't two currency codes
        # must not be mangled into a fake forex pair.
        self.assertEqual(normalize_symbol("ABCDEF"), "ABCDEF")

    def test_empty_input_passthrough(self):
        self.assertEqual(normalize_symbol(""), "")


@pytest.mark.unit
class TestNoMarketDataError(unittest.TestCase):
    def test_message_includes_resolution(self):
        err = NoMarketDataError("XAUUSD+", "GC=F", "no rows")
        self.assertIn("XAUUSD+", str(err))
        self.assertIn("GC=F", str(err))
        self.assertEqual(err.symbol, "XAUUSD+")
        self.assertEqual(err.canonical, "GC=F")

    def test_canonical_defaults_to_symbol(self):
        err = NoMarketDataError("FOOBAR")
        self.assertEqual(err.canonical, "FOOBAR")


@pytest.mark.unit
class TestIsYahooSafe(unittest.TestCase):
    def test_accepts_structural_chars(self):
        for sym in ("AAPL", "GC=F", "^GSPC", "BRK.B", "BTC-USD"):
            self.assertTrue(is_yahoo_safe(sym))

    def test_rejects_slash_and_space(self):
        for sym in ("a/b", "AA PL", ""):
            self.assertFalse(is_yahoo_safe(sym))


if __name__ == "__main__":
    unittest.main()
