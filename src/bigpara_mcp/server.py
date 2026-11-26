"""MCP server: unofficial read-only access to Bigpara market data."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import markets as _m

mcp = FastMCP("bigpara-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for Bigpara (bigpara.hurriyet.com.tr), \
Hürriyet's finance portal: live BIST stock quotes, FX rates vs TRY, \
gold prices, BIST indices, crypto and market movers, plus OHLC price \
history. Data comes from Bigpara's public JSON API \
(api-bigpara.hurriyet.com.tr) — no login, no API key. Prices are live \
market data; verify on the site before acting on them.\
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir
"""

_SOURCE = "bigpara.hurriyet.com.tr"
_DISCLAIMER = ("Unofficial read-only data from bigpara.hurriyet.com.tr; "
               "verify on the site before acting on it.")


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _clean_symbols(symbols: str) -> list[str]:
    seen: list[str] = []
    for raw in symbols.replace(";", ",").split(","):
        s = raw.strip().upper()
        if s and s not in seen:
            seen.append(s)
    return seen


@mcp.tool()
def bigpara_get_quote(symbols: str) -> str:
    """Live quote for 1-20 symbols, comma-separated (e.g. "THYAO,ASELS" \
or "USDTRY,EURTRY,XU100,GLDGR"). Works for BIST stocks, FX pairs, \
gold, indices, crypto and commodities. Unknown symbols are reported \
in not_found (the API silently drops them)."""
    syms = _clean_symbols(symbols)
    if not syms:
        return _ok({"error": "no symbols given — e.g. \"THYAO,USDTRY\""})
    if len(syms) > _m.MAX_SYMBOLS_PER_CALL:
        return _ok({"error": f"at most {_m.MAX_SYMBOLS_PER_CALL} symbols "
                             f"per call (got {len(syms)})"})
    try:
        payload = _http.fetch_current(syms)
    except _http.BigparaError as e:
        return _ok({"error": str(e)})
    return _ok(_m.parse_quotes(payload, syms))


@mcp.tool()
def bigpara_search_stocks(query: str, limit: int = 10) -> str:
    """Find BIST stocks by symbol or company name (e.g. "thyao", \
"hava", "banka"). Searches the full 661-stock BIST universe; \
returns up to `limit` matches (1-50)."""
    q = (query or "").strip()
    if not q:
        return _ok({"error": "empty query — e.g. \"thyao\" or \"hava\""})
    limit = max(1, min(int(limit), 50))
    try:
        payload = _http.fetch_trends("tv", _m.STOCK_UNIVERSE_TOP)
    except _http.BigparaError as e:
        return _ok({"error": str(e)})
    rows = _m.parse_trends(payload)["items"]
    hits = _m.search_stocks(rows, q)[:limit]
    return _ok({"query": q, "total_universe": len(rows),
                "count": len(hits), "matches": hits})


@mcp.tool()
def bigpara_market_movers(market: str = "stocks",
                          order: str = "gainers", top: int = 10) -> str:
    """Top BIST movers (market="stocks") or crypto movers \
(market="crypto"). order: "gainers" (biggest % up), "losers" \
(biggest % down), "volume" (most traded). top: 1-50."""
    market = (market or "stocks").strip().lower()
    order = (order or "gainers").strip().lower()
    if market not in ("stocks", "crypto"):
        return _ok({"error": f"unknown market {market!r} — "
                             "use \"stocks\" or \"crypto\""})
    api_order = {"gainers": "pdesc", "losers": "pasc",
                 "volume": "tv"}.get(order)
    if api_order is None:
        return _ok({"error": f"unknown order {order!r} — use \"gainers\", "
                             "\"losers\" or \"volume\""})
    top = max(1, min(int(top), 50))
    try:
        payload = _http.fetch_trends(api_order, top,
                                     crypto=(market == "crypto"))
    except _http.BigparaError as e:
        return _ok({"error": str(e)})
    out = _m.parse_trends(payload)
    return _ok({"market": market, "order": order, **out})


@mcp.tool()
def bigpara_gold_prices() -> str:
    """Live gold prices in TRY: gram, has, çeyrek/yarım/tam/ziynet, \
gremse, hamit, reşat, 14/18/22 ayar, külçe, plus ons altın (XAUUSD) \
and gümüş gram/ons. 20 products in one call."""
    try:
        payload = _http.fetch_current(_m.GOLD_SYMBOLS)
    except _http.BigparaError as e:
        return _ok({"error": str(e)})
    return _ok(_m.parse_quotes(payload, _m.GOLD_SYMBOLS))


@mcp.tool()
def bigpara_fx_rates() -> str:
    """Live FX rates vs TRY: USD, EUR, GBP, CHF, CAD, JPY, CNY, AED, \
KWD plus free-market AUD (SAUD), Danish/Norwegian/Swedish krona, \
ruble and riyal. 15 pairs in one call."""
    try:
        payload = _http.fetch_current(_m.FX_SYMBOLS)
    except _http.BigparaError as e:
        return _ok({"error": str(e)})
    return _ok(_m.parse_quotes(payload, _m.FX_SYMBOLS))


@mcp.tool()
def bigpara_price_history(symbol: str, range: str = "monthly",
                          points: int = 30) -> str:
    """OHLC price history for one symbol (stock, index, FX, gold, \
crypto). range: "daily" (intraday, hourly), "weekly", "monthly" \
or "yearly". points: how many bars to return (1-365; defaults \
per range: daily 24, weekly 7, monthly 30, yearly 365)."""
    sym = (symbol or "").strip().upper()
    if not sym:
        return _ok({"error": "no symbol given — e.g. \"THYAO\""})
    rng = (range or "monthly").strip().lower()
    if rng not in _m.CHART_RANGES:
        return _ok({"error": f"unknown range {rng!r} — use \"daily\", "
                             "\"weekly\", \"monthly\" or \"yearly\""})
    api_range, resolution, default_points = _m.CHART_RANGES[rng]
    points = max(1, min(int(points), 365))
    try:
        payload = _http.fetch_chart(sym, api_range, resolution, points)
        out = _m.parse_chart(payload)
    except _http.BigparaError as e:
        return _ok({"error": str(e)})
    except ValueError as e:
        return _ok({"error": str(e), "symbol": sym})
    return _ok({"symbol": sym, "range": rng, **out})


@mcp.tool()
def bigpara_health() -> str:
    """Check whether the Bigpara API is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
