"""Tests for baostock_loader: code format handling.

Ensures both baostock native (sh.601398) and tushare-style (601398.SH) codes work.
"""
from backtest.loaders.baostock_loader import _is_a_share


class TestIsAShareCodeFormat:
    """Verify _is_a_share accepts both baostock native and tushare-style codes."""

    def test_baostock_native_sh_format(self):
        """sh.601398 is the baostock-native format and should be recognized."""
        assert _is_a_share("sh.601398") is True
        assert _is_a_share("sh.600036") is True

    def test_baostock_native_sz_format(self):
        """sz.000001 is the baostock-native format and should be recognized."""
        assert _is_a_share("sz.000001") is True
        assert _is_a_share("sz.002594") is True

    def test_tushare_style_sh_suffix(self):
        """600036.SH is the tushare-style format and should be recognized."""
        assert _is_a_share("600036.SH") is True
        assert _is_a_share("601398.SH") is True

    def test_tushare_style_sz_suffix(self):
        """000001.SZ is the tushare-style format and should be recognized."""
        assert _is_a_share("000001.SZ") is True
        assert _is_a_share("002594.SZ") is True

    def test_case_insensitive(self):
        """Code format detection should be case-insensitive."""
        assert _is_a_share("SH.601398") is True
        assert _is_a_share("sh.601398") is True
        assert _is_a_share("601398.sh") is True
        assert _is_a_share("601398.SH") is True

    def test_rejects_non_a_share(self):
        """Non-A-share codes should be rejected."""
        assert _is_a_share("AAPL") is False
        assert _is_a_share("BRK.B") is False
        assert _is_a_share("BTC-USD") is False
        assert _is_a_share("") is False
        assert _is_a_share("just_random_text") is False

    def test_rejects_hk_and_us_codes(self):
        """Hong Kong (5-digit) and US stock codes should not match."""
        assert _is_a_share("00700") is False
        assert _is_a_share("AAPL") is False
        assert _is_a_share("TSLA") is False


class TestFetchOneCodeHandling:
    """Verify _fetch_one handles both baostock native and tushare-style codes.

    These tests are unit-level only — they don't make real network calls.
    """

    def test_baostock_native_passthrough(self):
        """baostock native format (sh.601398) should pass through unchanged."""
        from unittest.mock import MagicMock
        from backtest.loaders.baostock_loader import DataLoader

        loader = DataLoader()
        bs_mock = MagicMock()
        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.error_msg = "success"
        mock_rs.next.side_effect = [False]
        bs_mock.query_history_k_data_plus.return_value = mock_rs

        loader._fetch_one(bs_mock, "sh.601398", "2024-01-01", "2024-01-31")
        call_args = bs_mock.query_history_k_data_plus.call_args
        assert call_args[0][0] == "sh.601398"

    def test_tushare_style_converted(self):
        """tushare-style format (601398.SH) should be converted to sh.601398."""
        from unittest.mock import MagicMock
        from backtest.loaders.baostock_loader import DataLoader

        loader = DataLoader()
        bs_mock = MagicMock()
        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.error_msg = "success"
        mock_rs.next.side_effect = [False]
        bs_mock.query_history_k_data_plus.return_value = mock_rs

        loader._fetch_one(bs_mock, "601398.SH", "2024-01-01", "2024-01-31")
        call_args = bs_mock.query_history_k_data_plus.call_args
        assert call_args[0][0] == "sh.601398"

    def test_tushare_sz_style_converted(self):
        """tushare-style SZ (000001.SZ) should be converted to sz.000001."""
        from unittest.mock import MagicMock
        from backtest.loaders.baostock_loader import DataLoader

        loader = DataLoader()
        bs_mock = MagicMock()
        mock_rs = MagicMock()
        mock_rs.error_code = "0"
        mock_rs.error_msg = "success"
        mock_rs.next.side_effect = [False]
        bs_mock.query_history_k_data_plus.return_value = mock_rs

        loader._fetch_one(bs_mock, "000001.SZ", "2024-01-01", "2024-01-31")
        call_args = bs_mock.query_history_k_data_plus.call_args
        assert call_args[0][0] == "sz.000001"
