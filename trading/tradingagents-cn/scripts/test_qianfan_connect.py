#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick connectivity test for Baidu Qianfan (ERNIE) via the OpenAI-compatible adapter.

Usage:
  # 1) Put your keys in .env or environment variables:
  #    QIANFAN_ACCESS_KEY=your_ak
  #    QIANFAN_SECRET_KEY=your_sk
  # 2) Optionally set model (default: ERNIE-Speed-8K)
  #    QIANFAN_MODEL=ERNIE-Lite-8K
  # 3) Run:
  #    python scripts/test_qianfan_connect.py
"""
import os
import sys
import time
from typing import Optional

# Try to load .env if python-dotenv is available
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from langchain_core.messages import HumanMessage
from tradingagents.llm_adapters.openai_compatible_base import (
    create_openai_compatible_llm,
)


def getenv_stripped(key: str) -> Optional[str]:
    val = os.getenv(key)
    return val.strip() if isinstance(val, str) else val


def main() -> int:
    # 检查新的API Key环境变量
    api_key = getenv_stripped("QIANFAN_API_KEY")
    
    # 兼容检查旧的环境变量
    ak = getenv_stripped("QIANFAN_ACCESS_KEY")
    sk = getenv_stripped("QIANFAN_SECRET_KEY")
    model = getenv_stripped("QIANFAN_MODEL") or "ernie-3.5-8k"

    print("==== Qianfan Connectivity Test ====")
    print(f"Model           : {model}")
    print(f"QIANFAN_API_KEY set  : {'YES' if api_key else 'NO'}")
    print(f"ACCESS_KEY set  : {'YES' if ak else 'NO'}")
    print(f"SECRET_KEY set  : {'YES' if sk else 'NO'}")

    if not api_key and (not ak or not sk):
        print("[ERROR] QIANFAN_API_KEY is missing, or QIANFAN_ACCESS_KEY and/or QIANFAN_SECRET_KEY are missing.")
        print("Please set QIANFAN_API_KEY, or both QIANFAN_ACCESS_KEY and QIANFAN_SECRET_KEY in your .env file and re-run.")
        return 2

    try:
        # Instantiate adapter via unified factory (this will validate AK/SK)
        llm = create_openai_compatible_llm(
            provider="qianfan",
            model=model,
            temperature=0.2,
            max_tokens=64,
        )
        print("[OK] Adapter instantiated.")
    except Exception as e:
        print(f"[ERROR] Failed to instantiate adapter: {e}")
        return 3

    try:
        # Send a minimal prompt to verify connectivity
        prompt = "请只回复：连接成功"
        print("Sending test prompt to Qianfan ...")
        t0 = time.time()
        resp = llm.invoke([HumanMessage(content=prompt)])  # type: ignore
        dt = time.time() - t0

        # LangChain returns an AIMessage; try to read .content
        content = getattr(resp, "content", str(resp))
        trimmed = content[:200] if isinstance(content, str) else str(content)[:200]
        print("[OK] Response received (<=200 chars):")
        print(trimmed)
        print(f"Elapsed: {dt:.2f}s")
        print("Connectivity looks good.")
        return 0
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        import traceback
        traceback.print_exc()
        return 4


if __name__ == "__main__":
    sys.exit(main())