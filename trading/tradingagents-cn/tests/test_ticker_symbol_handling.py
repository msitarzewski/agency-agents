import unittest

from cli.utils import normalize_ticker_symbol


class TickerSymbolHandlingTests(unittest.TestCase):
    def test_normalize_ticker_symbol_preserves_exchange_suffix(self):
        self.assertEqual(normalize_ticker_symbol(" cnc.to "), "CNC.TO")

    def test_normalize_ticker_symbol_keeps_hk_suffix_uppercase(self):
        self.assertEqual(normalize_ticker_symbol(" 0700.hk "), "0700.HK")

    def test_normalize_ticker_symbol_keeps_a_share_digits(self):
        self.assertEqual(normalize_ticker_symbol(" 600036 "), "600036")


if __name__ == "__main__":
    unittest.main()
