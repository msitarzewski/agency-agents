def build_instrument_context(ticker: str) -> str:
    normalized_ticker = str(ticker).strip().upper()
    return (
        f"当前分析标的的精确股票代码是 `{normalized_ticker}`。"
        "在所有工具调用、分析报告、交易建议和最终结论中，都必须使用这个完全一致的股票代码。"
        "如果代码带有交易所后缀，例如 `.HK`、`.TO`、`.L`、`.T`，必须原样保留，绝对不能省略、改写或替换。"
    )
