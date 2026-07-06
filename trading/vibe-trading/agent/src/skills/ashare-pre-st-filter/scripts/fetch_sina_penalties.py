#!/usr/bin/env python3
"""新浪财经 A 股监管处罚记录抓取脚本（独立 stdlib 实现）。

用途：为 ashare-pre-st-filter skill 的 E2 证据面提供输入。

数据源：vip.stock.finance.sina.com.cn/corp/go.php/vGP_GetOutOfLine/stockid/<6位>.phtml
解析目标：HTML 表格 <table id="collectFund_1">，每条记录由 <thead>(类型/公告日期) + 4 行 (标题/批复原因/批复内容/处理人) 构成。

安全约束：
- SSRF 防护：仅允许 host == vip.stock.finance.sina.com.cn
- GBK 解码（新浪页面）
- 节流 + 指数退避重试

输出：JSON 到 stdout；失败时返回 {"source": "unavailable", "error": "..."}。
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
import unicodedata
from html.parser import HTMLParser
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ALLOWED_HOST = "vip.stock.finance.sina.com.cn"
URL_TEMPLATE = (
    "https://vip.stock.finance.sina.com.cn/corp/go.php/vGP_GetOutOfLine/stockid/{code6}.phtml"
)
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 15
MAX_RETRIES = 3
THROTTLE_SECONDS = 0.4

REASON_KEYWORDS = [
    ("信息披露违规", ["信息披露", "未及时披露", "未披露", "披露不", "披露违规"]),
    ("内幕交易", ["内幕交易", "内幕信息"]),
    ("市场操纵", ["操纵市场", "操纵股价", "操纵证券"]),
    ("财务造假", ["财务造假", "虚增收入", "虚增利润", "财务舞弊"]),
    ("虚假陈述", ["虚假记载", "虚假陈述", "误导性陈述"]),
    ("违规减持", ["违规减持", "短线交易", "违规增减持"]),
    ("占用资金", ["占用资金", "资金占用", "非经营性占用"]),
    ("违规担保", ["违规担保", "对外担保"]),
]

ISSUER_KEYWORDS = [
    ("上交所", ["上海证券交易所", "上交所"]),
    ("深交所", ["深圳证券交易所", "深交所"]),
    ("北交所", ["北京证券交易所", "北交所"]),
    # 地方证监局必须优先于证监会，否则"中国证监会北京监管局"会被误归为证监会。
    ("地方证监局", ["证监局"]),
    ("证监会", ["中国证券监督管理委员会", "证监会"]),
]

# 处罚主体识别。匹配优先级：shareholder > officer > company（默认）。
# 用于 E2 频次规则的权重折算——非公司主体（股东/董监高）权重 ×0.5，
# 因为这类处罚反映个人行为，不等同于"公司治理失序"。
#
# 优先级决策依据（CR P1-2）：身份叠加（如"董事长 X 兼控股股东"）时，
# 监管语境取最重责任主体——shareholder 责任高于 officer，故先扫 shareholder。
SUBJECT_KEYWORDS = [
    ("shareholder", [
        "控股股东", "实际控制人", "实控人", "原实际控制人", "原实控人",
        "持股5%以上", "持股 5%以上", "5%以上股东", "5%以上的股东",
        "第一大股东", "二股东", "大股东", "股东减持",
        "股东收到", "股东因", "原股东", "前股东", "一致行动人",
    ]),
    ("officer", [
        "董事长", "副董事长", "总经理", "副总经理", "总裁",
        "财务总监", "董事会秘书", "董秘", "证券事务代表",
        "监事会主席", "独立董事",
        "时任董事", "时任监事", "时任高管", "时任董秘",
        "高级管理人员", "高管人员", "聘任的高级管理人员",
    ]),
]

DATE_RE = re.compile(r"公告日期[:：]\s*(\d{4}-\d{1,2}-\d{1,2})")

SECURITY_MENTION_ONLY_KEYWORDS = [
    "证券从业",
    "证券账户",
    "控制使用",
    "持有并交易",
    "交易股票",
    "买入",
    "卖出",
    "账户交易",
]


def _norm_text(text: str) -> str:
    """文本归一化：NFKC 折叠全角/半角 + 去除内部空白。

    应用场景（CR P2）：新浪页面会出现“５％以上股东”、“控股 股东”等变体，
    原吝始“kw in text”会漏命中。归一化后“５％”→“5%”，中文间空格被吃掉。
    """
    if not text:
        return ""
    s = unicodedata.normalize("NFKC", text)
    return re.sub(r"\s+", "", s)


def _validate_stockid(ts_code: str) -> str:
    """从 600000.SH / 000001.SZ / 600000 中抽取 6 位股票代码。"""
    if not ts_code:
        raise ValueError("ts_code is required")
    s = ts_code.strip().upper()
    s = re.sub(r"\.(SH|SZ|BJ)$", "", s)
    if not re.fullmatch(r"\d{6}", s):
        raise ValueError(f"invalid ts_code: {ts_code!r} (expect 6-digit code)")
    return s


def _normalize_reason(text: str) -> str:
    if not text:
        return "unknown"
    norm = _norm_text(text)
    for label, kws in REASON_KEYWORDS:
        for kw in kws:
            if _norm_text(kw) in norm:
                return label
    return "unknown"


def _normalize_issuer(text: str) -> str:
    if not text:
        return "unknown"
    norm = _norm_text(text)
    for label, kws in ISSUER_KEYWORDS:
        for kw in kws:
            if _norm_text(kw) in norm:
                return label
    return "unknown"


def _normalize_subject(text: str) -> str:
    """从标题/原因/内容文本推断处罚主体。

    返回值：
    - "shareholder"  控股股东 / 实控人 / 5% 以上大股东
    - "officer"      董事 / 监事 / 高管（董秘、财务总监等）
    - "company"      默认；当文本无任何上述关键词时归为公司本身

    供 E2 频次规则做主体权重折算（非公司主体 ×0.5）。
    """
    if not text:
        return "company"
    norm = _norm_text(text)
    for label, kws in SUBJECT_KEYWORDS:
        for kw in kws:
            if _norm_text(kw) in norm:
                return label
    return "company"


def _build_target_aliases(stock_name: str | None, aliases: list[str] | None = None) -> list[str]:
    """Build normalized target-name aliases for relevance checks.

    Args:
        stock_name: Official short name from ``stock_basic.name``.
        aliases: Extra caller-provided aliases.

    Returns:
        Deduplicated normalized aliases.
    """
    candidates = [stock_name or "", *(aliases or [])]
    out: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        norm = _norm_text(candidate)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        out.append(norm)
    return out


def _contains_any_alias(text: str, aliases: list[str]) -> bool:
    norm = _norm_text(text)
    return bool(norm and any(alias in norm for alias in aliases))


def _classify_target_relevance(
    record: dict[str, Any],
    target_aliases: list[str],
) -> tuple[str, bool, str]:
    """Classify whether a Sina penalty record is countable for this stock.

    Args:
        record: Parsed penalty record.
        target_aliases: Normalized stock-name aliases.

    Returns:
        ``(target_relevance, e2_countable, relevance_reason)``.
    """
    if not target_aliases:
        return "unknown", True, "stock_name_not_provided"

    title = str(record.get("title") or "")
    reason = str(record.get("reason") or "")
    content = str(record.get("content") or "")
    combined = " ".join([title, reason, content])
    if not _contains_any_alias(combined, target_aliases):
        return "unknown", False, "target_alias_not_found"

    title_hits_target = _contains_any_alias(title, target_aliases)
    subject = str(record.get("subject_normalized") or "company")
    looks_like_security_mention = any(
        _norm_text(keyword) in _norm_text(combined)
        for keyword in SECURITY_MENTION_ONLY_KEYWORDS
    )

    if not title_hits_target and looks_like_security_mention:
        return "security_mention_only", False, "target_only_appears_in_security_trade_list"
    if subject in {"shareholder", "officer"}:
        return "related_party", True, f"target_named_with_{subject}"
    return "issuer_company", True, "target_named_as_company_record"


def _annotate_relevance(
    records: list[dict[str, Any]],
    target_aliases: list[str],
) -> list[dict[str, Any]]:
    """Add target relevance fields used by E2 frequency counting."""
    for rec in records:
        relevance, countable, reason = _classify_target_relevance(rec, target_aliases)
        rec["target_relevance"] = relevance
        rec["e2_countable"] = countable
        rec["relevance_reason"] = reason
        if relevance == "security_mention_only" and rec.get("subject_normalized") == "company":
            rec["subject_normalized"] = "unknown"
    return records


def _http_get_gbk(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"disallowed scheme: {parsed.scheme}")
    if parsed.hostname != ALLOWED_HOST:
        raise ValueError(f"disallowed host: {parsed.hostname}")

    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Encoding": "gzip",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                },
            )
            with urlopen(req, timeout=timeout) as resp:  # noqa: S310 — host is whitelisted
                raw = resp.read()
                if resp.headers.get("Content-Encoding", "").lower() == "gzip":
                    raw = gzip.decompress(raw)
            try:
                return raw.decode("gbk", errors="replace")
            except LookupError:
                return raw.decode("utf-8", errors="replace")
        except (HTTPError, URLError, TimeoutError) as exc:
            last_err = exc
            time.sleep(THROTTLE_SECONDS * (2 ** (attempt - 1)))
    raise RuntimeError(f"http get failed after {MAX_RETRIES} retries: {last_err}")


class _TableExtractor(HTMLParser):
    """提取 <table id="collectFund_1"> 的内部 HTML 文本（包含子标签）。"""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self._depth = 0
        self._capture = False
        self._buf: list[str] = []
        self.found: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            attrs_d = dict(attrs)
            if not self._capture and attrs_d.get("id") == "collectFund_1":
                self._capture = True
                self._depth = 1
                return
            if self._capture:
                self._depth += 1
        if self._capture:
            attr_str = "".join(f' {k}="{v}"' if v is not None else f" {k}" for k, v in attrs)
            self._buf.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag: str) -> None:
        if not self._capture:
            return
        if tag == "table":
            self._depth -= 1
            if self._depth <= 0:
                self.found = "".join(self._buf)
                self._capture = False
                return
        self._buf.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._capture:
            self._buf.append(data)

    def handle_entityref(self, name: str) -> None:
        if self._capture:
            self._buf.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._capture:
            self._buf.append(f"&#{name};")


# event_type 黑名单：head 文本首个中文片段如果落在这些"结构性字面量"上，
# 说明该 thead 没有显式标注事件类型，应回退到"未分类"。
# （CR P0-3：避免把"公告日期"误识别为 event_type，导致 E2 频次规则漏命中。）
_EVENT_TYPE_BLOCKLIST = {
    "公告日期", "日期", "批复", "批复内容", "批复原因",
    "处罚日期", "处罚原因", "处罚内容", "处罚机关",
    "标题", "处理人", "类型",
}


def _extract_event_type(head_text: str) -> str:
    """从 thead 文本中提取事件类型，跳过结构性字面量。"""
    for m in re.finditer(r"[\u4e00-\u9fa5]+", head_text):
        token = m.group(0)
        if token in _EVENT_TYPE_BLOCKLIST:
            continue
        return token
    return "未分类"


class _RecordParser(HTMLParser):
    """以 HTMLParser 切分 collectFund_1 表格中的单条记录。

    替代原 `_DATA_ROW_RE` + `_RECORD_HEAD_RE` 正则方案——后者
    在 `re.DOTALL + (?:(?!</tr>).)*?` 下属于灾难性回溯模式，
    遇到未闭合 `<tr>` 的脏 HTML 会指数级回溯（CR P0-1）。

    解析模型：
    - 状态机以 `<thead>` 为记录起点；遇到下一个 `<thead>` 落盘上一条。
    - 记录内的 `<tr>` 抓取 `<strong>KEY</strong>` 与同行第一个 `<td>VALUE</td>`。
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.records: list[dict[str, str]] = []
        self._cur: dict[str, Any] | None = None
        self._mode: str | None = None  # 'thead' | 'tr_key' | 'tr_val' | None
        self._buf: list[str] = []
        self._cur_key: str = ""
        self._val_captured: bool = False  # 同一 tr 内只取第一个 value td

    def _flush(self) -> None:
        if self._cur is not None:
            self.records.append(self._cur)
        self._cur = {"_head": "", "_fields": {}}

    def _capture(self, data: str) -> None:
        if self._mode in ("thead", "tr_key", "tr_val"):
            self._buf.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:  # noqa: ARG002
        if tag == "thead":
            self._flush()
            self._mode = "thead"
            self._buf = []
        elif tag == "tr":
            self._cur_key = ""
            self._val_captured = False
        elif tag == "strong" and self._mode not in ("thead", "tr_val"):
            # 仅在 row 起始（尚未进入 value td）时把 strong 视为 key；
            # 否则可能是 value 内的 <strong> 嵌套，应保留为 value 文本。
            self._mode = "tr_key"
            self._buf = []
        elif tag == "td":
            # 进入 td：仅当已读到 key 且本行尚未捕获 value 时切到 tr_val
            if self._mode != "thead" and self._cur_key and not self._val_captured:
                self._mode = "tr_val"
                self._buf = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "thead" and self._mode == "thead":
            head_text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if self._cur is None:
                self._cur = {"_head": "", "_fields": {}}
            self._cur["_head"] = head_text
            self._mode = None
            self._buf = []
        elif tag == "strong" and self._mode == "tr_key":
            self._cur_key = "".join(self._buf).strip().rstrip(":：")
            self._mode = None
            self._buf = []
        elif tag == "td" and self._mode == "tr_val":
            val = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if self._cur is not None and self._cur_key:
                self._cur["_fields"][self._cur_key] = val
            self._val_captured = True
            self._cur_key = ""
            self._mode = None
            self._buf = []
        elif tag == "tr":
            self._cur_key = ""
            self._val_captured = False

    def handle_data(self, data: str) -> None:
        self._capture(data)

    def close(self) -> None:  # type: ignore[override]
        super().close()
        # 落盘最后一条
        if self._cur is not None and (self._cur.get("_head") or self._cur.get("_fields")):
            self.records.append(self._cur)
            self._cur = None


def _build_record(raw: dict[str, Any]) -> dict[str, Any] | None:
    head = raw.get("_head") or ""
    fields: dict[str, str] = raw.get("_fields") or {}

    date_m = DATE_RE.search(head)
    ann_date = ""
    if date_m:
        try:
            y, mo, d = date_m.group(1).split("-")
            ann_date = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
        except Exception:
            ann_date = date_m.group(1)

    # event_type：先剥掉"公告日期: YYYY-MM-DD"再扫剩余首个中文片段；
    # 双重防御——剥不干净时再用黑名单兜底（CR P0-3）。
    head_wo_date = DATE_RE.sub("", head)
    head_wo_date = re.sub(r"公告日期[:：]?", "", head_wo_date)
    event_type = _extract_event_type(head_wo_date) or _extract_event_type(head)

    title = fields.get("标题", "")
    reason = fields.get("批复原因", "") or fields.get("处罚原因", "")
    content = fields.get("批复内容", "") or fields.get("处罚内容", "")
    issuer = fields.get("处理人", "") or fields.get("处罚机关", "")

    if not (title or reason or content):
        return None

    combined_for_reason = " ".join([title, reason, content])
    return {
        "ann_date": ann_date,
        "event_type": event_type,
        "title": title,
        "reason": reason,
        "reason_normalized": _normalize_reason(combined_for_reason),
        "content": content,
        "issuer": issuer,
        "issuer_normalized": _normalize_issuer(issuer),
        "subject_normalized": _normalize_subject(combined_for_reason),
    }


def _parse_penalty_list(html: str) -> list[dict[str, Any]]:
    extractor = _TableExtractor()
    extractor.feed(html)
    if not extractor.found:
        return []
    parser = _RecordParser()
    parser.feed(extractor.found)
    parser.close()
    out: list[dict[str, Any]] = []
    for raw in parser.records:
        rec = _build_record(raw)
        if rec is not None:
            out.append(rec)
    return out


def _apply_date_filter(
    records: list[dict[str, Any]],
    start_date: str | None,
    end_date: str | None,
) -> list[dict[str, Any]]:
    if not start_date and not end_date:
        return records
    out: list[dict[str, Any]] = []
    for rec in records:
        d = rec.get("ann_date") or ""
        if not d:
            # 公告日缺失时保留记录，但添加标记供 LLM 识别。
            rec.setdefault("_warning", "missing_ann_date")
            out.append(rec)
            continue
        if start_date and d < start_date:
            continue
        if end_date and d > end_date:
            continue
        out.append(rec)
    return out


def fetch_penalty_list(
    ts_code: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    stock_name: str | None = None,
    aliases: list[str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    code6 = _validate_stockid(ts_code)
    url = URL_TEMPLATE.format(code6=code6)
    try:
        html = _http_get_gbk(url, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return {
            "source": "unavailable",
            "ts_code": ts_code,
            "url": url,
            "error": f"http_failed: {exc}",
            "records": [],
        }
    try:
        records = _parse_penalty_list(html)
    except Exception as exc:  # noqa: BLE001
        return {
            "source": "unavailable",
            "ts_code": ts_code,
            "url": url,
            "error": f"parse_failed: {exc}",
            "records": [],
        }
    target_aliases = _build_target_aliases(stock_name, aliases)
    filtered = _apply_date_filter(_annotate_relevance(records, target_aliases), start_date, end_date)
    for rec in filtered:
        rec["source_url"] = url
    return {
        "source": "sina",
        "ts_code": ts_code,
        "url": url,
        "target_aliases": target_aliases,
        "start_date": start_date,
        "end_date": end_date,
        "total_in_page": len(records),
        "matched": len(filtered),
        "records": filtered,
    }


def _normalize_date_arg(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    m = re.fullmatch(r"(\d{4})[-/]?(\d{1,2})[-/]?(\d{1,2})", s)
    if not m:
        raise ValueError(f"invalid date: {s!r}")
    y, mo, d = m.groups()
    return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ts-code", required=True, help="例如 600000.SH / 000001.SZ / 688001")
    parser.add_argument("--stock-name", default=None, help="股票简称，例如 闻泰科技；用于过滤误召处罚记录")
    parser.add_argument(
        "--alias",
        action="append",
        default=[],
        help="额外目标别名；可重复传入",
    )
    parser.add_argument("--start-date", default=None, help="YYYY-MM-DD，含端点")
    parser.add_argument("--end-date", default=None, help="YYYY-MM-DD，含端点")
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="返回页面全量记录、忽略 --start-date / --end-date（推荐：由调用方在内存中切双窗口，避免两次 HTTP）",
    )
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args(argv)

    try:
        if args.no_filter:
            start_date = None
            end_date = None
        else:
            start_date = _normalize_date_arg(args.start_date)
            end_date = _normalize_date_arg(args.end_date)
    except ValueError as exc:
        print(json.dumps({"source": "unavailable", "error": str(exc)}, ensure_ascii=False))
        return 2

    try:
        result = fetch_penalty_list(
            args.ts_code,
            start_date=start_date,
            end_date=end_date,
            stock_name=args.stock_name,
            aliases=args.alias,
            timeout=args.timeout,
        )
    except ValueError as exc:
        # _validate_stockid 等参数校验异常：保持脚本契约
        # （永远输出 JSON，不抛 traceback），返回非零退出码。
        json.dump(
            {"source": "unavailable", "ts_code": args.ts_code, "error": f"invalid_input: {exc}", "records": []},
            sys.stdout,
            ensure_ascii=False,
            indent=args.indent,
        )
        sys.stdout.write("\n")
        return 2
    json.dump(result, sys.stdout, ensure_ascii=False, indent=args.indent)
    sys.stdout.write("\n")
    return 0 if result.get("source") == "sina" else 1


if __name__ == "__main__":
    raise SystemExit(main())
