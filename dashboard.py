"""
dashboard.py — Polymarket LP Bot terminal dashboard.

Serves a live web terminal on http://localhost:8001
Design mirrors copytrader.py (DEUS VULT style): dark glass, DM Mono,
tabs (Overview / Trades / Analytics / Log), Chart.js P&L curve.

Run:
    pip install fastapi uvicorn
    python dashboard.py

Bot writes trades to bot_trades.csv; this server reads that file every 3 s
and pushes state to all connected WebSocket clients.
"""

import asyncio
import csv
import io
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response

LOG_FILE   = os.environ.get("BOT_TRADES_CSV", "bot_trades.csv")
HOST       = os.environ.get("DASHBOARD_HOST", "0.0.0.0")
PORT       = int(os.environ.get("DASHBOARD_PORT", "8003"))
REFRESH_MS = 3000

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(broadcaster())
    yield

app     = FastAPI(lifespan=lifespan)
clients: list[WebSocket] = []


# ── Data helpers ───────────────────────────────────────────────────────────────

def _read_csv() -> list[dict]:
    p = Path(LOG_FILE)
    if not p.exists():
        return []
    try:
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            return [r for r in reader if r.get("success", "").lower() == "true"]
    except Exception:
        return []


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _fmt_ts(ts_str: str) -> str:
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.strftime("%H:%M:%S")
    except Exception:
        return str(ts_str)[:8]


def build_state(rows: list[dict]) -> dict:
    buys    = [r for r in rows if r.get("side") == "BUY"]
    # Treat both SETTLE and TP (take-profit) rows as closed positions
    settles = [r for r in rows if r.get("side") in ("SETTLE", "TP")]

    def _is_win(r: dict) -> bool:
        if r.get("side") == "TP":
            return _safe_float(r.get("pnl_usdc")) > 0
        return _safe_float(r.get("fill_price")) >= 0.99

    wins   = [s for s in settles if _is_win(s)]
    losses = [s for s in settles if not _is_win(s)]

    # A position is closed if we have any SETTLE or TP exit for that market+outcome
    settled_keys = {(s["market_id"], s["outcome"]) for s in settles}
    open_buys = [b for b in buys if (b.get("market_id",""), b.get("outcome","")) not in settled_keys]

    total_pnl      = sum(_safe_float(s.get("pnl_usdc")) for s in settles)
    total_invested = sum(_safe_float(b.get("size_usdc")) for b in buys)
    open_exposure  = sum(_safe_float(b.get("size_usdc")) for b in open_buys)
    win_payout     = sum(_safe_float(w.get("size_usdc")) for w in wins)

    n_settled = len(wins) + len(losses)
    win_rate  = round(len(wins) / n_settled * 100, 1) if n_settled else 0

    mode = rows[-1].get("mode", "PAPER").upper() if rows else "PAPER"

    # Open positions grouped by market+outcome
    open_pos_map: dict[tuple, dict] = {}
    for b in open_buys:
        key = (b.get("market_id", ""), b.get("outcome", ""))
        if key not in open_pos_map:
            open_pos_map[key] = {
                "title":       _short_q(b.get("question", "")),
                "outcome":     b.get("outcome", ""),
                "side":        b.get("outcome", ""),
                "cost":        0.0,
                "tokens":      0.0,
                "entry_price": 0.0,
                "n":           0,
                "end_ts":      _safe_float(b.get("market_end_ts")),
            }
        p = open_pos_map[key]
        p["cost"]   += _safe_float(b.get("size_usdc"))
        p["tokens"] += _safe_float(b.get("tokens"))
        p["entry_price"] += _safe_float(b.get("fill_price"))
        p["n"] += 1

    open_positions = []
    for (mid, out), p in open_pos_map.items():
        avg_entry = p["entry_price"] / p["n"] if p["n"] else 0
        open_positions.append({
            "title":       p["title"],
            "outcome":     p["outcome"],
            "side":        p["side"],
            "cost":        round(p["cost"], 2),
            "tokens":      round(p["tokens"], 4),
            "entry_price": round(avg_entry, 4),
            "time":        _fmt_time_left(p["end_ts"]),
        })

    # Trade history list (newest first, last 200)
    trade_history = []
    for r in reversed(rows[-200:]):
        side = r.get("side", "")
        pnl  = _safe_float(r.get("pnl_usdc"))
        if side == "SETTLE":
            fp = _safe_float(r.get("fill_price"))
            status = "settled"
            result = "win" if fp >= 0.99 else "loss"
        elif side == "TP":
            status = "settled"
            result = "win" if _safe_float(r.get("pnl_usdc")) > 0 else "loss"
        else:
            status = "open" if (r.get("market_id",""), r.get("outcome","")) not in settled_keys else "settled"
            result = ""

        trade_history.append({
            "id":          r.get("timestamp", ""),
            "time":        _fmt_ts(r.get("timestamp", "")),
            "title":       _short_q(r.get("question", "")),
            "outcome":     r.get("outcome", ""),
            "side":        r.get("outcome", ""),
            "size_usdc":   round(_safe_float(r.get("size_usdc")), 2),
            "entry_price": round(_safe_float(r.get("fill_price")), 4),
            "pnl":         round(pnl, 2),
            "status":      status,
            "result":      result,
            "end_ts":      _safe_float(r.get("market_end_ts")),
            "trade_side":  side,
        })

    # P&L curve points (settled only, cumulative)
    pnl_curve = []
    cum = 0.0
    for s in settles:
        cum += _safe_float(s.get("pnl_usdc"))
        pnl_curve.append(round(cum, 4))

    # Entry price win-rate buckets (for chart)
    price_buckets: dict[int, dict] = {}
    for s in settles:
        ep = _safe_float(s.get("price"))
        b  = int(ep * 10) * 10
        if b not in price_buckets:
            price_buckets[b] = {"w": 0, "l": 0}
        fp = _safe_float(s.get("fill_price"))
        if fp >= 0.99:
            price_buckets[b]["w"] += 1
        else:
            price_buckets[b]["l"] += 1

    last_trade = None
    if rows:
        lb = next((r for r in reversed(rows) if r.get("side") == "BUY"), None)
        if lb:
            last_trade = {
                "title":   _short_q(lb.get("question", "")),
                "outcome": lb.get("outcome", ""),
                "our_bet": round(_safe_float(lb.get("size_usdc")), 2),
                "price":   round(_safe_float(lb.get("fill_price")), 4),
                "time":    _fmt_ts(lb.get("timestamp", "")),
            }

    return {
        "running":        True,
        "dry_run":        mode != "LIVE",
        "mode":           mode,
        "pnl":            round(total_pnl, 2),
        "wins":           len(wins),
        "losses":         len(losses),
        "win_rate":       win_rate,
        "total_trades":   len(buys),
        "total_invested": round(total_invested, 2),
        "win_payout":     round(win_payout, 2),
        "open_exposure":  round(open_exposure, 2),
        "open_positions": open_positions,
        "last_trade":     last_trade,
        "trade_history":  trade_history,
        "pnl_curve":      pnl_curve,
        "price_buckets":  price_buckets,
        "logs":           [],  # bot logs not wired here
        "ts":             datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


def _short_q(q: str) -> str:
    if not q:
        return "—"
    for pfx in ("Up or Down - ", "up or down - "):
        if pfx in q:
            q = q.split(pfx, 1)[-1]
    return q[:55]


def _fmt_time_left(end_ts: float) -> str:
    if not end_ts:
        return "—"
    secs = int(end_ts - time.time())
    if secs <= 0:
        return "EXPIRED"
    m, s = divmod(secs, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m:02d}m"
    return f"{m}m {s:02d}s"


# ── WebSocket broadcaster ──────────────────────────────────────────────────────

async def broadcaster():
    while True:
        await asyncio.sleep(REFRESH_MS / 1000)
        if not clients:
            continue
        rows  = _read_csv()
        state = build_state(rows)
        dead  = []
        for ws in list(clients):
            try:
                await ws.send_json({"type": "state", "data": state})
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in clients:
                clients.remove(ws)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/export")
async def export_trades():
    rows = _read_csv()
    buf  = io.StringIO()
    fields = ["timestamp","market","outcome","entry_price","size_usdc","tokens",
              "market_end_ts","payout_price","pnl_usdc","settled_at","result"]
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    # Include both SETTLE and TP (take-profit) rows as exit events
    settles = {
        (r["market_id"], r["outcome"]): r
        for r in rows if r.get("side") in ("SETTLE", "TP")
    }
    for r in rows:
        if r.get("side") != "BUY":
            continue
        key = (r.get("market_id",""), r.get("outcome",""))
        s   = settles.get(key)
        if s:
            if s.get("side") == "TP":
                is_win = _safe_float(s.get("pnl_usdc")) > 0
            else:
                fp = _safe_float(s["fill_price"])
                is_win = fp >= 0.99
            result = "WIN" if is_win else "LOSS"
        else:
            result = "OPEN"
        w.writerow({
            "timestamp":   r.get("timestamp",""),
            "market":      _short_q(r.get("question","")),
            "outcome":     r.get("outcome",""),
            "entry_price": r.get("fill_price",""),
            "size_usdc":   r.get("size_usdc",""),
            "tokens":      r.get("tokens",""),
            "market_end_ts": r.get("market_end_ts",""),
            "payout_price":  s["fill_price"] if s else "",
            "pnl_usdc":      s["pnl_usdc"]   if s else "",
            "settled_at":    s["timestamp"]   if s else "",
            "result":        result,
        })
    fname = f"bot_trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={fname}"},
    )


@app.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    # Send initial state immediately
    rows  = _read_csv()
    state = build_state(rows)
    await websocket.send_json({"type": "init", "state": state})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return DASHBOARD


# ── HTML / CSS / JS ───────────────────────────────────────────────────────────

DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LP Bot &#9670; Terminal</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Outfit:wght@400;500;600;700;800&display=swap');
  *{box-sizing:border-box;margin:0;padding:0}
  :root{
    --bg:#07080d;--s1:rgba(255,255,255,0.04);--s2:rgba(255,255,255,0.07);--s3:rgba(255,255,255,0.11);
    --b1:rgba(255,255,255,0.07);--b2:rgba(255,255,255,0.13);
    --tx:#dde1ed;--tx2:#7c839a;--tx3:#40455a;
    --grn:#2dd4a0;--grn-d:rgba(45,212,160,0.12);
    --red:#f16b6b;--red-d:rgba(241,107,107,0.12);
    --blu:#5ba0f5;--blu-d:rgba(91,160,245,0.12);
    --amb:#f5b731;--amb-d:rgba(245,183,49,0.12);
    --pur:#9d7ef0;--pur-d:rgba(157,126,240,0.12);
    --r:12px;--r-sm:7px;
    --mono:'DM Mono',monospace;--ui:'Outfit',sans-serif;
  }
  html,body{height:100%;background:var(--bg);color:var(--tx);font-family:var(--ui);font-size:13px}
  body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
    background:radial-gradient(ellipse 60% 40% at 0% 0%,rgba(157,126,240,0.06) 0%,transparent 60%),
               radial-gradient(ellipse 50% 35% at 100% 100%,rgba(45,212,160,0.05) 0%,transparent 60%)}
  ::-webkit-scrollbar{width:3px;height:3px}
  ::-webkit-scrollbar-thumb{background:var(--b2);border-radius:2px}
  #app{position:relative;z-index:1;height:100vh;display:flex;flex-direction:column;overflow:hidden}

  /* TOPBAR */
  #topbar{display:flex;align-items:center;justify-content:space-between;padding:10px 18px;gap:12px;flex-shrink:0;
    border-bottom:1px solid var(--b1);background:rgba(7,8,13,0.9);backdrop-filter:blur(20px)}
  .tls{display:flex;gap:5px}
  .tl{width:11px;height:11px;border-radius:50%}
  .brand{font-size:14px;font-weight:800;letter-spacing:-0.3px}
  .brand-sub{font-size:9px;color:var(--tx3);letter-spacing:0.6px;text-transform:uppercase;display:flex;align-items:center;gap:5px;margin-top:1px}
  .run-dot{width:7px;height:7px;border-radius:50%;background:var(--red)}
  .pill{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:100px;font-size:9px;font-weight:700;letter-spacing:0.5px;text-transform:uppercase}
  .pill-dry{background:var(--amb-d);color:var(--amb);border:1px solid rgba(245,183,49,0.2)}
  .pill-live{background:var(--red-d);color:var(--red);border:1px solid rgba(241,107,107,0.2);animation:pulse 2s infinite}
  .pill-paper{background:var(--blu-d);color:var(--blu);border:1px solid rgba(91,160,245,0.2)}
  .pill-dot{width:4px;height:4px;border-radius:50%;background:currentColor}
  .conn-dot{width:7px;height:7px;border-radius:50%;background:var(--red);transition:background .3s}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
  @keyframes blink{0%,100%{opacity:.8}50%{opacity:0}}

  /* TABS */
  #tabs{display:flex;gap:2px;padding:0 18px;border-bottom:1px solid var(--b1);flex-shrink:0;background:rgba(7,8,13,0.7)}
  .tab{padding:9px 16px;font-size:11px;font-weight:600;color:var(--tx3);cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;letter-spacing:0.2px}
  .tab:hover{color:var(--tx2)}
  .tab.active{color:var(--tx);border-bottom-color:var(--pur)}

  /* PANELS */
  .panel{display:none;flex:1;overflow:hidden}
  .panel.active{display:flex}

  /* OVERVIEW */
  #p-overview{flex-direction:row;overflow:hidden}
  #ov-left{width:310px;flex-shrink:0;border-right:1px solid var(--b1);overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px}
  #chart-area{flex:1;display:flex;flex-direction:column;overflow:hidden;padding:14px;gap:12px}

  .card{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);padding:13px}
  .card-title{font-size:9px;font-weight:700;letter-spacing:0.8px;text-transform:uppercase;color:var(--tx3);margin-bottom:10px}
  .stats-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px}
  .stat{background:var(--s2);border-radius:var(--r-sm);padding:9px 11px}
  .stat-label{font-size:9px;color:var(--tx3);text-transform:uppercase;letter-spacing:0.4px;margin-bottom:3px}
  .stat-val{font-size:19px;font-weight:800;font-family:var(--mono);letter-spacing:-0.5px;font-variant-numeric:tabular-nums}

  .pos-list{display:flex;flex-direction:column;gap:5px;max-height:200px;overflow-y:auto}
  .pos-row{background:var(--s2);border:1px solid var(--b1);border-radius:var(--r-sm);padding:9px}
  .pos-header{display:flex;justify-content:space-between;align-items:center;gap:6px;margin-bottom:3px}
  .pos-title{font-size:11px;font-weight:600;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .pos-badge{font-size:8px;font-weight:800;padding:2px 6px;border-radius:4px;text-transform:uppercase;letter-spacing:0.4px}
  .pos-badge.up{background:var(--grn-d);color:var(--grn);border:1px solid rgba(45,212,160,0.18)}
  .pos-badge.down{background:var(--red-d);color:var(--red);border:1px solid rgba(241,107,107,0.18)}
  .pos-meta{font-size:10px;color:var(--tx3);font-family:var(--mono);display:flex;gap:10px}

  .lt-title{font-size:12px;font-weight:600;margin-bottom:7px;line-height:1.4}
  .lt-grid{display:grid;grid-template-columns:auto 1fr;gap:3px 10px;font-size:10px;font-family:var(--mono)}
  .lt-k{color:var(--tx3)} .lt-v{color:var(--tx2)}

  .chart-wrap{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);padding:14px;flex:1;min-height:0;display:flex;flex-direction:column;gap:8px}
  .chart-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;flex-shrink:0}
  .chart-sm{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);padding:12px;height:180px;display:flex;flex-direction:column}
  .chart-sm canvas{flex:1;min-height:0}
  canvas{width:100%!important}
  .chart-label{font-size:9px;font-weight:700;letter-spacing:0.6px;text-transform:uppercase;color:var(--tx3);margin-bottom:8px}

  /* TRADES PANEL */
  #p-trades{flex-direction:column;overflow:hidden}
  #trades-toolbar{display:flex;align-items:center;gap:10px;padding:10px 16px;border-bottom:1px solid var(--b1);flex-shrink:0;flex-wrap:wrap}
  .tb-label{font-size:10px;color:var(--tx3);text-transform:uppercase;letter-spacing:0.4px}
  .filter-btn{padding:4px 10px;border-radius:6px;font-size:10px;font-weight:600;cursor:pointer;border:1px solid var(--b1);background:var(--s1);color:var(--tx2);transition:all .15s}
  .filter-btn.active{background:var(--pur-d);border-color:rgba(157,126,240,0.3);color:var(--pur)}
  .export-btn{margin-left:auto;padding:5px 14px;border-radius:7px;font-size:10px;font-weight:700;cursor:pointer;
    border:1px solid rgba(45,212,160,0.3);background:var(--grn-d);color:var(--grn);text-decoration:none;transition:all .15s;letter-spacing:0.3px}
  .export-btn:hover{background:rgba(45,212,160,0.2)}
  #trades-table-wrap{flex:1;overflow-y:auto;padding:0 0 8px}
  table{width:100%;border-collapse:collapse;font-size:11px}
  thead th{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:var(--tx3);
    padding:8px 14px;border-bottom:1px solid var(--b1);text-align:left;
    position:sticky;top:0;background:rgba(7,8,13,0.95);backdrop-filter:blur(10px)}
  tbody td{padding:9px 14px;border-bottom:1px solid rgba(255,255,255,0.03);font-family:var(--mono);vertical-align:middle}
  tbody tr:hover td{background:var(--s1)}
  .badge{display:inline-block;padding:2px 6px;border-radius:4px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.3px}
  .b-win{background:var(--grn-d);color:var(--grn);border:1px solid rgba(45,212,160,0.2)}
  .b-loss{background:var(--red-d);color:var(--red);border:1px solid rgba(241,107,107,0.2)}
  .b-open{background:var(--amb-d);color:var(--amb);border:1px solid rgba(245,183,49,0.2)}
  .b-up{background:var(--grn-d);color:var(--grn)} .b-down{background:var(--red-d);color:var(--red)}
  .b-buy{background:var(--blu-d);color:var(--blu)} .b-settle{background:var(--pur-d);color:var(--pur)}
  .empty-state{text-align:center;padding:48px;color:var(--tx3);font-size:12px}

  /* ANALYTICS PANEL */
  #p-analytics{flex-direction:column;overflow-y:auto;padding:16px;gap:14px}
  .analytics-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px}
  .ana-card{background:var(--s1);border:1px solid var(--b1);border-radius:var(--r);padding:14px}
  .ana-title{font-size:9px;font-weight:700;letter-spacing:0.7px;text-transform:uppercase;color:var(--tx3);margin-bottom:10px}
  .ana-val{font-size:24px;font-weight:800;font-family:var(--mono);letter-spacing:-0.5px}
  .ana-sub{font-size:10px;color:var(--tx3);margin-top:3px;font-family:var(--mono)}
  .bar-row{display:flex;align-items:center;gap:8px;margin-bottom:5px;font-size:10px;font-family:var(--mono)}
  .bar-label{color:var(--tx2);min-width:70px;font-size:9px}
  .bar-track{flex:1;height:6px;background:var(--s3);border-radius:3px;overflow:hidden}
  .bar-fill-w{height:100%;border-radius:3px;background:var(--grn)}
  .bar-fill-l{height:100%;border-radius:3px;background:var(--red)}
  .bar-count{color:var(--tx3);min-width:20px;text-align:right;font-size:9px}

  /* LOG PANEL */
  #log-wrap{display:flex;flex-direction:column;flex:1;overflow:hidden}
  #log-header{display:flex;align-items:center;justify-content:space-between;padding:9px 16px;border-bottom:1px solid var(--b1);flex-shrink:0}
  #log-area{flex:1;overflow-y:auto;padding:6px 0;font-family:var(--mono);font-size:11px}
  .log-row{display:flex;align-items:baseline;gap:7px;padding:3px 14px;transition:background .1s}
  .log-row:hover{background:var(--s1)}
  .log-ts{color:var(--tx3);flex-shrink:0;font-size:10px;min-width:55px}
  .log-tag-pill{font-size:8px;font-weight:700;padding:1px 5px;border-radius:3px;text-transform:uppercase;letter-spacing:0.4px;flex-shrink:0;min-width:40px;text-align:center}
  .log-msg{color:var(--tx2);flex:1;line-height:1.5}
  .lp-INFO{background:var(--s2);color:var(--tx3)} .lp-BUY{background:var(--blu-d);color:var(--blu)}
  .lp-WIN{background:var(--grn-d);color:var(--grn)} .lp-LOSS{background:var(--red-d);color:var(--red)}
  .lp-SETTLE{background:var(--pur-d);color:var(--pur)} .lp-OPEN{background:var(--amb-d);color:var(--amb)}
  .tag-WIN .log-msg{color:var(--grn)} .tag-LOSS .log-msg{color:var(--red)} .tag-BUY .log-msg{color:#93c5fd}
</style>
</head>
<body>
<div id="app">

  <!-- TOPBAR -->
  <div id="topbar">
    <div style="display:flex;align-items:center;gap:12px">
      <div class="tls">
        <div class="tl" style="background:#ff5f57"></div>
        <div class="tl" style="background:#febc2e"></div>
        <div class="tl" style="background:#28c840"></div>
      </div>
      <div>
        <div class="brand">&#9670; Polymarket LP Bot</div>
        <div class="brand-sub">
          <span id="run-dot" class="run-dot"></span>
          <span id="run-lbl" style="color:var(--tx3)">Connecting...</span>
          <span style="color:var(--tx3)">|</span>
          <span id="ts-disp" style="color:var(--tx3);font-family:var(--mono);font-size:9px">--</span>
        </div>
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px">
      <span id="mode-pill" class="pill pill-paper"><span class="pill-dot"></span><span id="mode-txt">Paper</span></span>
      <div style="display:flex;align-items:center;gap:5px">
        <div id="conn-d" class="conn-dot"></div>
        <span id="conn-lbl" style="color:var(--tx3);font-size:10px">Disconnected</span>
      </div>
    </div>
  </div>

  <!-- TABS -->
  <div id="tabs">
    <div class="tab active"  onclick="switchTab('overview')">Overview</div>
    <div class="tab"         onclick="switchTab('trades')">Trades</div>
    <div class="tab"         onclick="switchTab('analytics')">Analytics</div>
    <div class="tab"         onclick="switchTab('log')">Log</div>
  </div>

  <!-- OVERVIEW -->
  <div id="p-overview" class="panel active">
    <div id="ov-left">
      <div class="card">
        <div class="card-title">Performance</div>
        <div class="stats-grid">
          <div class="stat"><div class="stat-label">P&amp;L</div><div class="stat-val" id="s-pnl">&#8212;</div></div>
          <div class="stat"><div class="stat-label">Win Rate</div><div class="stat-val" id="s-wr">&#8212;</div></div>
          <div class="stat"><div class="stat-label">Record</div><div class="stat-val" id="s-wl" style="font-size:13px;padding-top:4px">&#8212;</div></div>
          <div class="stat"><div class="stat-label">Trades</div><div class="stat-val" id="s-total">0</div></div>
          <div class="stat"><div class="stat-label">Open Exp.</div><div class="stat-val" id="s-exp" style="font-size:14px;padding-top:2px">&#8212;</div></div>
          <div class="stat"><div class="stat-label">Invested</div><div class="stat-val" id="s-inv" style="font-size:14px;padding-top:2px">&#8212;</div></div>
        </div>
      </div>

      <div class="card">
        <div class="card-title">Last Trade</div>
        <div id="lt-empty" style="color:var(--tx3);font-size:11px;text-align:center;padding:10px">Waiting for first trade...</div>
        <div id="lt-fill" style="display:none">
          <div class="lt-title" id="lt-title">&#8212;</div>
          <div class="lt-grid">
            <span class="lt-k">Outcome</span><span class="lt-v" id="lt-outcome">&#8212;</span>
            <span class="lt-k">Our bet</span><span class="lt-v" id="lt-our">&#8212;</span>
            <span class="lt-k">Entry</span><span class="lt-v" id="lt-price">&#8212;</span>
            <span class="lt-k">Time</span><span class="lt-v" id="lt-time">&#8212;</span>
          </div>
        </div>
      </div>

      <div class="card" style="flex:1">
        <div class="card-title">Open Positions (<span id="pos-count">0</span>)</div>
        <div class="pos-list" id="pos-list">
          <div style="color:var(--tx3);font-size:11px;text-align:center;padding:14px">No open positions</div>
        </div>
      </div>
    </div>

    <div id="chart-area">
      <div class="chart-wrap">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span class="chart-label">P&amp;L Curve</span>
          <span id="chart-pnl-badge" style="font-size:12px;font-weight:800;font-family:var(--mono)">&#8212;</span>
        </div>
        <canvas id="pnlChart"></canvas>
      </div>
      <div class="chart-row">
        <div class="chart-sm">
          <div class="chart-label">Win rate by entry price</div>
          <canvas id="priceChart"></canvas>
        </div>
        <div class="chart-sm">
          <div class="chart-label">Open positions exposure ($)</div>
          <canvas id="expChart"></canvas>
        </div>
      </div>
    </div>
  </div>

  <!-- TRADES -->
  <div id="p-trades" class="panel">
    <div id="trades-toolbar">
      <span class="tb-label">Filter:</span>
      <div class="filter-btn active" onclick="setFilter('all',this)">All</div>
      <div class="filter-btn" onclick="setFilter('open',this)">Open</div>
      <div class="filter-btn" onclick="setFilter('win',this)">Wins</div>
      <div class="filter-btn" onclick="setFilter('loss',this)">Losses</div>
      <span id="trade-count" style="font-size:10px;color:var(--tx3);font-family:var(--mono)">0 trades</span>
      <a class="export-btn" href="/export" download>&#8595; Export CSV</a>
    </div>
    <div id="trades-table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th><th>Market</th><th>Outcome</th>
            <th>Type</th><th>Size ($)</th><th>Entry</th>
            <th>Expires</th><th>P&amp;L</th><th>Status</th>
          </tr>
        </thead>
        <tbody id="trades-tbody"></tbody>
      </table>
      <div id="trades-empty" class="empty-state" style="display:none">No trades yet — start the bot: python run_bot.py</div>
    </div>
  </div>

  <!-- ANALYTICS -->
  <div id="p-analytics" class="panel" style="flex-direction:column;overflow-y:auto;padding:16px;gap:14px">
    <div class="analytics-grid">
      <div class="ana-card"><div class="ana-title">Total P&amp;L</div><div class="ana-val" id="a-pnl">&#8212;</div><div class="ana-sub">realised</div></div>
      <div class="ana-card"><div class="ana-title">Win Rate</div><div class="ana-val" id="a-wr">&#8212;</div><div class="ana-sub">settled trades</div></div>
      <div class="ana-card"><div class="ana-title">Total Wins</div><div class="ana-val" id="a-wins" style="color:var(--grn)">0</div><div class="ana-sub">winning settlements</div></div>
      <div class="ana-card"><div class="ana-title">Total Losses</div><div class="ana-val" id="a-losses" style="color:var(--red)">0</div><div class="ana-sub">losing settlements</div></div>
      <div class="ana-card"><div class="ana-title">Total Invested</div><div class="ana-val" id="a-inv">&#8212;</div><div class="ana-sub">USDC deployed</div></div>
      <div class="ana-card"><div class="ana-title">Open Exposure</div><div class="ana-val" id="a-exp" style="color:var(--amb)">&#8212;</div><div class="ana-sub">unsettled positions</div></div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
      <div class="ana-card">
        <div class="ana-title">Win rate by outcome (UP / DOWN)</div>
        <div id="a-by-side" style="margin-top:4px"></div>
      </div>
      <div class="ana-card">
        <div class="ana-title">Win rate by entry price bucket</div>
        <div id="a-by-price" style="margin-top:4px"></div>
      </div>
    </div>
  </div>

  <!-- LOG -->
  <div id="p-log" class="panel">
    <div id="log-wrap">
      <div id="log-header">
        <span style="font-size:11px;font-weight:700">Trade Activity</span>
        <span id="log-ct" style="font-size:10px;color:var(--tx3)">0 events</span>
      </div>
      <div id="log-area"></div>
    </div>
  </div>

</div>
<script>
let trades=[], activeTab='overview', tradeFilter='all';
let pnlChart=null, priceChart=null, expChart=null;

// ── TABS ──────────────────────────────────────────────────────────────────────
function switchTab(t){
  activeTab=t;
  document.querySelectorAll('.tab').forEach((el,i)=>
    el.classList.toggle('active',['overview','trades','analytics','log'][i]===t));
  document.querySelectorAll('.panel').forEach(el=>el.classList.remove('active'));
  document.getElementById('p-'+t).classList.add('active');
  if(t==='analytics') renderAnalytics();
  if(t==='trades')    renderTradesTable();
  if(t==='log')       renderLog();
}

// ── WEBSOCKET ─────────────────────────────────────────────────────────────────
function connect(){
  const ws=new WebSocket('ws://'+location.host+'/ws');
  ws.onopen=()=>setConn(true);
  ws.onmessage=ev=>{
    const m=JSON.parse(ev.data);
    if(m.type==='init'||m.type==='state'){
      const d=m.state||m.data;
      trades=d.trade_history||[];
      updateState(d);
    }
  };
  ws.onclose=()=>{setConn(false);setTimeout(connect,2500);};
  ws.onerror=()=>setConn(false);
}
function setConn(v){
  document.getElementById('conn-d').style.background=v?'var(--grn)':'var(--red)';
  document.getElementById('conn-lbl').textContent=v?'Connected':'Disconnected';
  document.getElementById('conn-lbl').style.color=v?'var(--grn)':'var(--tx3)';
}

// ── STATE UPDATE ──────────────────────────────────────────────────────────────
function updateState(s){
  document.getElementById('ts-disp').textContent=s.ts||'';
  const rd=document.getElementById('run-dot');
  rd.style.background='var(--grn)';rd.style.animation='pulse 1.5s infinite';
  document.getElementById('run-lbl').textContent='Running';
  document.getElementById('run-lbl').style.color='var(--grn)';

  const mp=document.getElementById('mode-pill');
  if(s.mode==='LIVE'){mp.className='pill pill-live';}
  else if(s.dry_run){mp.className='pill pill-dry';}
  else{mp.className='pill pill-paper';}
  document.getElementById('mode-txt').textContent=s.mode||'PAPER';

  const pnl=parseFloat(s.pnl)||0;
  const pe=document.getElementById('s-pnl');
  pe.textContent=(pnl>=0?'+$':'-$')+Math.abs(pnl).toFixed(2);
  pe.style.color=pnl>0?'var(--grn)':pnl<0?'var(--red)':'var(--tx2)';

  const wr=parseFloat(s.win_rate)||0;
  const we=document.getElementById('s-wr');
  we.textContent=wr.toFixed(0)+'%';
  we.style.color=wr>=50?'var(--grn)':'var(--red)';

  document.getElementById('s-wl').textContent=(s.wins||0)+'W / '+(s.losses||0)+'L';
  document.getElementById('s-total').textContent=s.total_trades||0;

  const exp=parseFloat(s.open_exposure)||0;
  document.getElementById('s-exp').textContent='$'+exp.toFixed(2);
  document.getElementById('s-inv').textContent='$'+(parseFloat(s.total_invested)||0).toFixed(2);

  // Last trade
  const lt=s.last_trade;
  if(lt){
    document.getElementById('lt-empty').style.display='none';
    document.getElementById('lt-fill').style.display='block';
    document.getElementById('lt-title').textContent=lt.title||'—';
    document.getElementById('lt-outcome').textContent=lt.outcome||'—';
    document.getElementById('lt-our').textContent='$'+(lt.our_bet||0).toFixed(2);
    document.getElementById('lt-price').textContent=((lt.price||0)*100).toFixed(1)+'¢';
    document.getElementById('lt-time').textContent=lt.time||'—';
  }

  // Open positions
  const positions=s.open_positions||[];
  document.getElementById('pos-count').textContent=positions.length;
  const pl=document.getElementById('pos-list');
  if(!positions.length){
    pl.innerHTML='<div style="color:var(--tx3);font-size:11px;text-align:center;padding:14px">No open positions</div>';
  } else {
    pl.innerHTML=positions.map(p=>{
      const cls=p.outcome.toLowerCase()==='up'?'up':'down';
      return `<div class="pos-row">
        <div class="pos-header">
          <div class="pos-title">${p.title||'?'}</div>
          <div class="pos-badge ${cls}">${p.outcome}</div>
        </div>
        <div class="pos-meta">
          <span>$${parseFloat(p.cost).toFixed(2)} @ ${(parseFloat(p.entry_price)*100).toFixed(1)}¢</span>
          <span style="margin-left:auto">${p.time||''}</span>
        </div>
      </div>`;
    }).join('');
  }

  updateCharts(s);

  if(activeTab==='trades')    renderTradesTable();
  if(activeTab==='analytics') renderAnalytics();
  if(activeTab==='log')       renderLog();
}

// ── CHARTS ────────────────────────────────────────────────────────────────────
const gc={color:'rgba(255,255,255,0.05)'};
const tc={color:'#40455a',font:{family:"'DM Mono'",size:10}};

function updateCharts(s){
  // P&L curve
  const pts=s.pnl_curve||[];
  if(!pnlChart){
    const ctx=document.getElementById('pnlChart').getContext('2d');
    pnlChart=new Chart(ctx,{type:'line',data:{
      labels:pts.map((_,i)=>i+1),
      datasets:[{data:pts,borderColor:'#2dd4a0',borderWidth:1.5,pointRadius:0,tension:0.3,
        fill:true,backgroundColor:'rgba(45,212,160,0.06)'}]
    },options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{display:false}},
      scales:{x:{grid:gc,ticks:{...tc,maxTicksLimit:6}},y:{grid:gc,ticks:tc}}}});
  } else {
    pnlChart.data.labels=pts.map((_,i)=>i+1);
    pnlChart.data.datasets[0].data=pts;
    pnlChart.update('none');
  }
  const lastPnl=pts.length?pts[pts.length-1]:0;
  const badge=document.getElementById('chart-pnl-badge');
  badge.textContent=(lastPnl>=0?'+$':'-$')+Math.abs(lastPnl).toFixed(2);
  badge.style.color=lastPnl>=0?'var(--grn)':'var(--red)';

  // Win rate by price bucket
  const pb=s.price_buckets||{};
  const bKeys=Object.keys(pb).sort((a,b)=>+a-+b);
  const wData=bKeys.map(k=>pb[k].w);
  const lData=bKeys.map(k=>pb[k].l);
  const bLabels=bKeys.map(k=>k+'¢');
  if(!priceChart){
    const ctx=document.getElementById('priceChart').getContext('2d');
    priceChart=new Chart(ctx,{type:'bar',data:{labels:bLabels,datasets:[
      {label:'Win',data:wData,backgroundColor:'rgba(45,212,160,0.5)',borderRadius:3},
      {label:'Loss',data:lData,backgroundColor:'rgba(241,107,107,0.5)',borderRadius:3}
    ]},options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{display:false}},
      scales:{x:{stacked:true,grid:gc,ticks:tc},y:{stacked:true,grid:gc,ticks:tc}}}});
  } else {
    priceChart.data.labels=bLabels;
    priceChart.data.datasets[0].data=wData;
    priceChart.data.datasets[1].data=lData;
    priceChart.update('none');
  }

  // Open exposure by outcome
  const op=s.open_positions||[];
  const upExp=op.filter(p=>p.outcome==='Up').reduce((a,p)=>a+p.cost,0);
  const DownExp=op.filter(p=>p.outcome==='Down').reduce((a,p)=>a+p.cost,0);
  if(!expChart){
    const ctx=document.getElementById('expChart').getContext('2d');
    expChart=new Chart(ctx,{type:'doughnut',data:{
      labels:['Up','Down'],
      datasets:[{data:[upExp,DownExp],backgroundColor:['rgba(45,212,160,0.7)','rgba(241,107,107,0.7)'],borderWidth:0}]
    },options:{responsive:true,maintainAspectRatio:false,animation:false,
      plugins:{legend:{position:'bottom',labels:{color:'#40455a',font:{family:"'DM Mono'",size:10}}}}}});
  } else {
    expChart.data.datasets[0].data=[upExp,DownExp];
    expChart.update('none');
  }
}

// ── TRADES TABLE ──────────────────────────────────────────────────────────────
function setFilter(f,el){
  tradeFilter=f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  el.classList.add('active');
  renderTradesTable();
}

function fmtExpiry(ts){
  if(!ts) return '—';
  const now=Date.now()/1000;
  const secs=Math.floor(ts-now);
  if(secs<=0) return '<span style="color:var(--tx3)">EXPIRED</span>';
  const m=Math.floor(secs/60),s=secs%60,h=Math.floor(m/60);
  const cls=secs<60?'color:var(--red)':secs<120?'color:var(--amb)':'color:var(--grn)';
  return h?`<span style="${cls}">${h}h ${m%60}m</span>`:
           `<span style="${cls}">${m}m ${s.toString().padStart(2,'0')}s</span>`;
}

function renderTradesTable(){
  let rows=trades;
  if(tradeFilter==='open')  rows=trades.filter(t=>t.status==='open');
  if(tradeFilter==='win')   rows=trades.filter(t=>t.result==='win');
  if(tradeFilter==='loss')  rows=trades.filter(t=>t.result==='loss');

  document.getElementById('trade-count').textContent=rows.length+' trades';
  const empty=document.getElementById('trades-empty');
  const tbody=document.getElementById('trades-tbody');

  if(!rows.length){
    tbody.innerHTML=''; empty.style.display='block'; return;
  }
  empty.style.display='none';
  tbody.innerHTML=rows.map(t=>{
    const sideCls=t.trade_side==='BUY'?'b-buy':t.trade_side==='SETTLE'?'b-settle':'';
    const outCls=t.outcome?.toLowerCase()==='up'?'b-up':'b-down';
    const stBadge=t.result==='win'?'<span class="badge b-win">WIN</span>':
                  t.result==='loss'?'<span class="badge b-loss">LOSS</span>':
                  '<span class="badge b-open">OPEN</span>';
    const pnlStr=t.pnl&&t.result?
      `<span style="color:${t.result==='win'?'var(--grn)':'var(--red)'}">${t.result==='win'?'+':''}$${Math.abs(t.pnl).toFixed(2)}</span>`
      :'<span style="color:var(--tx3)">—</span>';
    return `<tr>
      <td style="color:var(--tx3)">${t.time}</td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${t.title}</td>
      <td><span class="badge ${outCls}">${t.outcome}</span></td>
      <td><span class="badge ${sideCls}">${t.trade_side}</span></td>
      <td>$${t.size_usdc.toFixed(2)}</td>
      <td>${(t.entry_price*100).toFixed(1)}¢</td>
      <td>${fmtExpiry(t.end_ts)}</td>
      <td>${pnlStr}</td>
      <td>${stBadge}</td>
    </tr>`;
  }).join('');
}

// ── ANALYTICS ─────────────────────────────────────────────────────────────────
function renderAnalytics(){
  const wins=trades.filter(t=>t.result==='win');
  const losses=trades.filter(t=>t.result==='loss');
  const settled=[...wins,...losses];
  const total=settled.length;
  const wr=total?(wins.length/total*100):0;
  const pnl=trades.reduce((a,t)=>a+(t.pnl||0),0);

  const fmt=v=>v>=0?`<span style="color:var(--grn)">+$${v.toFixed(2)}</span>`:
                    `<span style="color:var(--red)">-$${Math.abs(v).toFixed(2)}</span>`;

  document.getElementById('a-pnl').innerHTML=fmt(pnl);
  const we=document.getElementById('a-wr');
  we.textContent=wr.toFixed(0)+'%';
  we.style.color=wr>=50?'var(--grn)':'var(--red)';
  document.getElementById('a-wins').textContent=wins.length;
  document.getElementById('a-losses').textContent=losses.length;

  const inv=trades.filter(t=>t.trade_side==='BUY').reduce((a,t)=>a+t.size_usdc,0);
  document.getElementById('a-inv').textContent='$'+inv.toFixed(2);
  const exp=trades.filter(t=>t.status==='open').reduce((a,t)=>a+t.size_usdc,0);
  document.getElementById('a-exp').textContent='$'+exp.toFixed(2);

  // By side
  const bySide={Up:{w:0,l:0},Down:{w:0,l:0}};
  settled.forEach(t=>{if(bySide[t.outcome])t.result==='win'?bySide[t.outcome].w++:bySide[t.outcome].l++;});
  let sideHtml='';
  ['Up','Down'].forEach(s=>{
    const d=bySide[s];const tot=d.w+d.l;if(!tot)return;
    const wPct=tot?Math.round(d.w/tot*100):0;
    sideHtml+=`<div class="bar-row">
      <div class="bar-label">${s}</div>
      <div class="bar-track"><div class="bar-fill-w" style="width:${wPct}%"></div></div>
      <div class="bar-count">${wPct}%</div>
    </div>`;
  });
  document.getElementById('a-by-side').innerHTML=sideHtml||'<div style="color:var(--tx3);font-size:11px">No data yet</div>';

  // By price bucket
  const buckets={};
  settled.forEach(t=>{
    const b=Math.floor(t.entry_price*10)*10;
    if(!buckets[b])buckets[b]={w:0,l:0};
    t.result==='win'?buckets[b].w++:buckets[b].l++;
  });
  let prHtml='';
  Object.keys(buckets).sort((a,b)=>+a-+b).forEach(k=>{
    const d=buckets[k];const tot=d.w+d.l;if(!tot)return;
    const wPct=Math.round(d.w/tot*100);
    prHtml+=`<div class="bar-row">
      <div class="bar-label">${k}¢</div>
      <div class="bar-track"><div class="bar-fill-w" style="width:${wPct}%"></div></div>
      <div class="bar-count">${wPct}%</div>
    </div>`;
  });
  document.getElementById('a-by-price').innerHTML=prHtml||'<div style="color:var(--tx3);font-size:11px">No data yet</div>';
}

// ── LOG ───────────────────────────────────────────────────────────────────────
function renderLog(){
  const recent=trades.slice(0,100);
  const la=document.getElementById('log-area');
  la.innerHTML=recent.map(t=>{
    const tag=t.trade_side==='SETTLE'?(t.result==='win'?'WIN':'LOSS'):t.trade_side||'INFO';
    const msg=t.trade_side==='BUY'
      ? `BUY ${t.outcome} — ${t.title} @ ${(t.entry_price*100).toFixed(1)}¢  $${t.size_usdc.toFixed(2)}`
      : t.trade_side==='SETTLE'
      ? `SETTLE ${t.outcome} — ${t.title} | ${t.result?.toUpperCase()} | pnl: ${t.pnl>=0?'+':''}$${(t.pnl||0).toFixed(2)}`
      : `${t.title}`;
    return `<div class="log-row tag-${tag}">
      <span class="log-ts">${t.time}</span>
      <span class="log-tag-pill lp-${tag}">${tag}</span>
      <span class="log-msg">${msg}</span>
    </div>`;
  }).join('');
  document.getElementById('log-ct').textContent=recent.length+' events';
}

// ── INIT ──────────────────────────────────────────────────────────────────────
connect();
// Refresh expiry timers on open positions every second
setInterval(()=>{
  if(activeTab==='trades'&&tradeFilter==='open') renderTradesTable();
  document.querySelectorAll('.pos-meta span:last-child').forEach(el=>{
    // live update skipped for brevity — WS refresh handles it
  });
},1000);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
