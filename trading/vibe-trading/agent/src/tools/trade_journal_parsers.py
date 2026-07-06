"""Trade journal format adapters.

Each parser normalizes one broker export format into a list of TradeRecord.
Supported: Tonghuashun (同花顺), Eastmoney (东方财富), Futu (富途), generic CSV.

Encoding fallback order for CSV: utf-8 → utf-8-sig → gbk → gb2312.
Excel (.xlsx/.xls) always opens as utf-8 internally via openpyxl/xlrd.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

FormatName = str  # "tonghuashun" | "eastmoney" | "futu" | "generic" | "unknown"

_A_SHARE_EXCHANGE_MAP = {
    # prefix → suffix; Shanghai Main + STAR, Shenzhen Main + SME + ChiNext, BSE
    ("6",): ".SH",
    ("0", "3"): ".SZ",
    ("4", "8"): ".BJ",
}

_BUY_TOKENS = {"buy", "b", "买入", "证券买入", "融资买入", "做多", "long"}
_SELL_TOKENS = {"sell", "s", "卖出", "证券卖出", "融券卖出", "做空", "short"}


@dataclass(frozen=True)
class TradeRecord:
    """Standardized trade record (immutable).

    Attributes:
        datetime: ISO8601 timestamp, e.g. "2026-01-15 09:35:00".
        symbol: Exchange-qualified symbol, e.g. "600519.SH" / "AAPL" / "BTC-USDT".
        name: Human-readable instrument name.
        side: "buy" or "sell".
        quantity: Filled quantity.
        price: Filled price.
        amount: Gross amount (quantity * price, pre-fee).
        fee: Total fees (commission + stamp + transfer).
        market: "china_a" / "us" / "hk" / "crypto" / "other".
    """

    datetime: str
    symbol: str
    name: str
    side: str
    quantity: float
    price: float
    amount: float
    fee: float
    market: str


# ---------------- File loading ----------------

def load_dataframe(path: str | Path) -> pd.DataFrame:
    """Load a CSV/Excel file into a DataFrame with encoding fallback.

    Args:
        path: Path to the file (.csv/.xlsx/.xls).

    Returns:
        Parsed DataFrame with raw column names (no normalization).

    Raises:
        FileNotFoundError: File does not exist.
        ValueError: Unsupported extension or all encodings failed.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    ext = p.suffix.lower()
    if ext in {".xlsx", ".xls"}:
        return pd.read_excel(p, dtype=str)
    if ext != ".csv":
        raise ValueError(f"Unsupported extension: {ext}")

    last_err: Exception | None = None
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb2312"):
        try:
            return pd.read_csv(p, dtype=str, encoding=enc)
        except UnicodeDecodeError as exc:
            last_err = exc
    raise ValueError(f"Failed to decode CSV with utf-8/gbk/gb2312: {last_err}")


# ---------------- Format detection ----------------

def detect_format(df: pd.DataFrame) -> FormatName:
    """Detect broker format by column-name signature.

    Args:
        df: Raw DataFrame from load_dataframe.

    Returns:
        Format identifier; "unknown" when nothing matches (caller may still
        try GenericCSVParser).
    """
    cols = set(df.columns.astype(str))

    if {"成交时间", "证券代码", "操作"}.issubset(cols):
        return "tonghuashun"
    if {"买卖标志", "股票代码"}.issubset(cols) or {"买卖标志", "成交均价"}.issubset(cols):
        return "eastmoney"
    if {"Date", "Symbol", "Side"}.issubset(cols) or {"Date", "Symbol", "Direction"}.issubset(cols):
        return "futu"

    # Generic: any subset containing time/symbol/side hints
    lowered = {c.lower() for c in cols}
    if any(c in lowered for c in ("datetime", "time", "date")) and any(
        c in lowered for c in ("symbol", "ticker", "code")
    ):
        return "generic"
    return "unknown"


# ---------------- Parsers ----------------

def _normalize_side(raw: Any) -> str:
    """Return 'buy'/'sell', falling back to 'buy'."""
    s = str(raw).strip().lower()
    if s in _SELL_TOKENS or any(tok in s for tok in _SELL_TOKENS):
        return "sell"
    return "buy"


def _qualify_a_share(code: str) -> str:
    """Append .SH/.SZ/.BJ suffix to a bare A-share ticker."""
    code = str(code).strip().zfill(6)
    if "." in code:
        return code.upper()
    first = code[0]
    for prefixes, suffix in _A_SHARE_EXCHANGE_MAP.items():
        if first in prefixes:
            return code + suffix
    return code


def _to_float(val: Any, default: float = 0.0) -> float:
    """Safely cast to float; return default on failure."""
    if val is None:
        return default
    try:
        s = str(val).replace(",", "").strip()
        return float(s) if s else default
    except (ValueError, TypeError):
        return default


def parse_tonghuashun(df: pd.DataFrame) -> list[TradeRecord]:
    """Parse 同花顺 exports.

    Expected columns: 成交时间, 证券代码, 证券名称, 操作, 成交数量, 成交价格,
    成交金额, 手续费, 印花税, 过户费.
    """
    records: list[TradeRecord] = []
    for _, row in df.iterrows():
        qty = _to_float(row.get("成交数量"))
        price = _to_float(row.get("成交价格"))
        amount = _to_float(row.get("成交金额")) or qty * price
        fee = _to_float(row.get("手续费")) + _to_float(row.get("印花税")) + _to_float(row.get("过户费"))
        records.append(TradeRecord(
            datetime=str(row.get("成交时间", "")).strip(),
            symbol=_qualify_a_share(row.get("证券代码", "")),
            name=str(row.get("证券名称", "")).strip(),
            side=_normalize_side(row.get("操作")),
            quantity=qty,
            price=price,
            amount=amount,
            fee=fee,
            market="china_a",
        ))
    return records


def parse_eastmoney(df: pd.DataFrame) -> list[TradeRecord]:
    """Parse 东方财富 exports.

    Expected columns: 成交日期 (YYYYMMDD), 成交时间 (HH:MM:SS), 股票代码,
    股票名称, 买卖标志 (B/S), 成交数量, 成交均价, 成交金额, 佣金, 印花税.
    """
    records: list[TradeRecord] = []
    for _, row in df.iterrows():
        raw_date = str(row.get("成交日期", "")).strip()
        raw_time = str(row.get("成交时间", "")).strip()
        if len(raw_date) == 8 and raw_date.isdigit():
            iso_date = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
        else:
            iso_date = raw_date
        dt = f"{iso_date} {raw_time}".strip()
        qty = _to_float(row.get("成交数量"))
        price = _to_float(row.get("成交均价"))
        amount = _to_float(row.get("成交金额")) or qty * price
        fee = _to_float(row.get("佣金")) + _to_float(row.get("印花税"))
        records.append(TradeRecord(
            datetime=dt,
            symbol=_qualify_a_share(row.get("股票代码", "")),
            name=str(row.get("股票名称", "")).strip(),
            side=_normalize_side(row.get("买卖标志")),
            quantity=qty,
            price=price,
            amount=amount,
            fee=fee,
            market="china_a",
        ))
    return records


def _futu_market(symbol: str, market_hint: str) -> str:
    """Infer market from symbol/market column."""
    hint = market_hint.strip().lower()
    if hint in {"hk", "us", "cn"}:
        return {"hk": "hk", "us": "us", "cn": "china_a"}[hint]
    if symbol.endswith(".HK"):
        return "hk"
    if symbol.isalpha() or "." not in symbol:
        return "us"
    return "other"


def parse_futu(df: pd.DataFrame) -> list[TradeRecord]:
    """Parse 富途 exports (English headers, HK+US mix).

    Expected columns: Date, Time, Symbol, Name, Side, Quantity, Price,
    Amount, Commission, Platform Fee, Market (optional).
    """
    records: list[TradeRecord] = []
    for _, row in df.iterrows():
        date = str(row.get("Date", "")).strip()
        time = str(row.get("Time", "")).strip()
        dt = f"{date} {time}".strip()
        symbol = str(row.get("Symbol", "")).strip().upper()
        qty = _to_float(row.get("Quantity"))
        price = _to_float(row.get("Price"))
        amount = _to_float(row.get("Amount")) or qty * price
        fee = _to_float(row.get("Commission")) + _to_float(row.get("Platform Fee"))
        records.append(TradeRecord(
            datetime=dt,
            symbol=symbol,
            name=str(row.get("Name", "")).strip(),
            side=_normalize_side(row.get("Side") if "Side" in df.columns else row.get("Direction")),
            quantity=qty,
            price=price,
            amount=amount,
            fee=fee,
            market=_futu_market(symbol, str(row.get("Market", ""))),
        ))
    return records


def parse_generic(df: pd.DataFrame) -> list[TradeRecord]:
    """Parse a generic CSV with lowercase English headers.

    Matches columns case-insensitively. Expected (any alias in parens):
        datetime (time/date+time), symbol (ticker/code), name, side (direction),
        quantity (qty/size), price, amount (value/notional), fee (commission).
    """
    colmap: dict[str, str] = {}
    for col in df.columns:
        key = str(col).strip().lower()
        colmap[key] = col

    def pick(*names: str) -> str | None:
        for n in names:
            if n in colmap:
                return colmap[n]
        return None

    dt_col = pick("datetime", "time")
    date_col = pick("date")
    sym_col = pick("symbol", "ticker", "code")
    name_col = pick("name", "instrument")
    side_col = pick("side", "direction", "action")
    qty_col = pick("quantity", "qty", "size", "volume")
    price_col = pick("price")
    amount_col = pick("amount", "value", "notional")
    fee_col = pick("fee", "commission", "fees")

    records: list[TradeRecord] = []
    for _, row in df.iterrows():
        if dt_col:
            dt = str(row.get(dt_col, "")).strip()
        elif date_col:
            dt = str(row.get(date_col, "")).strip()
        else:
            dt = ""
        symbol = str(row.get(sym_col, "")).strip() if sym_col else ""
        qty = _to_float(row.get(qty_col)) if qty_col else 0.0
        price = _to_float(row.get(price_col)) if price_col else 0.0
        amount = _to_float(row.get(amount_col)) if amount_col else qty * price
        fee = _to_float(row.get(fee_col)) if fee_col else 0.0
        market = _infer_market_from_symbol(symbol)
        records.append(TradeRecord(
            datetime=dt,
            symbol=symbol.upper(),
            name=str(row.get(name_col, "")).strip() if name_col else "",
            side=_normalize_side(row.get(side_col) if side_col else "buy"),
            quantity=qty,
            price=price,
            amount=amount or qty * price,
            fee=fee,
            market=market,
        ))
    return records


def _infer_market_from_symbol(symbol: str) -> str:
    """Best-effort market inference from a symbol string."""
    s = symbol.upper()
    if s.endswith(".HK"):
        return "hk"
    if s.endswith(".SH") or s.endswith(".SZ") or s.endswith(".BJ"):
        return "china_a"
    if "-" in s and any(quote in s for quote in ("USDT", "USDC", "BTC", "USD")):
        return "crypto"
    if s.isalpha():
        return "us"
    return "other"


_PARSERS = {
    "tonghuashun": parse_tonghuashun,
    "eastmoney": parse_eastmoney,
    "futu": parse_futu,
    "generic": parse_generic,
}


def parse_file(path: str | Path) -> tuple[FormatName, list[TradeRecord]]:
    """End-to-end: load file, detect format, parse.

    Args:
        path: File path.

    Returns:
        (format_name, records). Falls back to generic if detection is unknown
        but columns look parsable; otherwise raises ValueError.

    Raises:
        ValueError: Unknown format with no usable columns.
    """
    df = load_dataframe(path)
    fmt = detect_format(df)
    if fmt == "unknown":
        try:
            records = parse_generic(df)
            if records and records[0].symbol:
                return "generic", records
        except Exception:
            pass
        raise ValueError(f"Unrecognized trade journal format. Columns: {list(df.columns)}")
    return fmt, _PARSERS[fmt](df)


def records_to_dataframe(records: list[TradeRecord]) -> pd.DataFrame:
    """Convert records to a standardized DataFrame (datetime column parsed)."""
    if not records:
        return pd.DataFrame(columns=[f.name for f in TradeRecord.__dataclass_fields__.values()])
    df = pd.DataFrame([asdict(r) for r in records])
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    return df.sort_values("datetime").reset_index(drop=True)
