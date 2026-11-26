"""Pure parsing/normalisation for Bigpara market data.

All functions here take already-fetched JSON (dict) and return plain
dicts/lists — no I/O, so the offline tests run against recorded
fixtures without touching the network.
"""
from __future__ import annotations

from datetime import datetime, timezone

# Gold products as listed on bigpara.hurriyet.com.tr/altin/ (verified
# live 2026-11-26). Names come from the API's own `desc` field at
# runtime; the symbols are fixed here so one call returns the shelf.
GOLD_SYMBOLS = [
    "GLDGR",        # Gram altın (TL)
    "GLDHAS",       # Has altın gram
    "SGLDC",        # Çeyrek altın
    "SGLDY",        # Yarım altın
    "SGLDT",        # Tam altın
    "SGZIYNET",     # Ziynet altın
    "GLDZIYNET2_5",  # Kapalıçarşı ziynet 2.5
    "GLDZIYNET5LI",  # Kapalıçarşı ziynet 5'li
    "SGGREMSE",     # Gremse altın
    "SGHAMIT",      # Hamit altın (serbest piyasa)
    "SRES",         # Reşat altın
    "SRESK",        # Kulplu reşat altın
    "GPOR14",       # 14 ayar altın TL/gr
    "GPOR18",       # 18 ayar altın TL/gr
    "GPOR22",       # 22 ayar altın TL/gr
    "BILEZIKAKAYNAK",  # Eski bilezik (22 ayar)
    "USGLD",        # Külçe altın (dolar)
    "XAUUSD",       # Ons altın (USD)
    "SXAGGR",       # Gümüş gram (TL)
    "XAGUSD",       # Gümüş ons (USD)
]

# FX pairs vs TRY as listed on bigpara.hurriyet.com.tr/doviz/
# (verified live 2026-11-26). SAUD is the site's own symbol for the
# Australian dollar (free market); SDKK/SNOK/SRUB/SSAR/SSEK are the
# free-market krone/ruble/riyal/krona symbols.
FX_SYMBOLS = [
    "USDTRY", "EURTRY", "GBPTRY", "CHFTRY", "CADTRY", "JPYTRY",
    "CNYTRY", "AEDTRY", "KWDTRY", "SAUD", "SDKK", "SNOK",
    "SRUB", "SSAR", "SSEK",
]

# Major BIST indices (bigpara.hurriyet.com.tr/borsa/endeksler/).
INDEX_SYMBOLS = [
    "XU100", "XU030", "XBANK", "XGIDA", "XHOLD", "XFINK", "XSPOR",
    "XMADN", "XELKT", "XINSA", "XGMYO", "XKMYA", "XHARZ", "XSBAL",
    "XSTKR", "XUTUM",
]

MAX_SYMBOLS_PER_CALL = 20  # API 400s on over-long Symbols values

# range -> (api range, resolution, default points)
CHART_RANGES = {
    "daily": ("daily", "1h", 24),
    "weekly": ("weekly", "1d", 7),
    "monthly": ("monthly", "1d", 30),
    "yearly": ("yearly", "1d", 365),
}

# The trends endpoint returns the whole BIST universe when Top is
# large; totalCount was 661 on 2026-11-26.
STOCK_UNIVERSE_TOP = 700


def _ts_to_iso(ts) -> str | None:
    """Millisecond epoch -> ISO 8601 UTC, or None when absent/invalid."""
    try:
        return datetime.fromtimestamp(float(ts) / 1000,
                                      tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _name(row: dict) -> str | None:
    """Best human name: desc, else the ds2 short label, else None."""
    return row.get("desc") or row.get("ds2") or None


def parse_quote(row: dict) -> dict:
    """Normalise one /api/trade/current row.

    API fields: s (symbol), desc/ds2 (name), url (Bigpara detail
    page), ts (ms epoch), b/a (bid/ask), o/h/l/c (open/high/low/
    last close), yc (previous close), ch (change), p (change %),
    tv (volume, shares), tt (turnover, TRY), wa (weighted avg),
    prec (decimals), ms (market segment: Equity/Currency/Index/
    Cryptocurrency/...).
    """
    return {
        "symbol": row.get("s"),
        "name": _name(row),
        "market": row.get("ms"),
        "price": row.get("c"),
        "bid": row.get("b"),
        "ask": row.get("a"),
        "open": row.get("o"),
        "high": row.get("h"),
        "low": row.get("l"),
        "prev_close": row.get("yc"),
        "change": row.get("ch"),
        "change_pct": row.get("p"),
        "volume": row.get("tv"),
        "turnover_try": row.get("tt"),
        "weighted_avg": row.get("wa"),
        "decimals": row.get("prec"),
        "as_of": _ts_to_iso(row.get("ts")),
        "url": ("https://bigpara.hurriyet.com.tr" + row["url"]
                if row.get("url") else None),
    }


def parse_quotes(payload: dict, requested: list[str]) -> dict:
    """Normalise a /api/trade/current payload.

    The API silently drops unknown symbols from `data` (success
    stays true, errors stays []) — so the caller reports them via
    `not_found` instead of trusting the payload.
    """
    rows = payload.get("data") or []
    quotes = [parse_quote(r) for r in rows if isinstance(r, dict)]
    found = {q["symbol"].upper() for q in quotes if q.get("symbol")}
    not_found = [s for s in requested if s.upper() not in found]
    return {"quotes": quotes, "not_found": not_found,
            "count": len(quotes)}


def parse_trends(payload: dict) -> dict:
    """Normalise a /api/trade/trends or /api/crypto/trends payload."""
    rows = payload.get("data") or []
    return {
        "total": payload.get("totalCount"),
        "count": len(rows),
        "items": [parse_quote(r) for r in rows if isinstance(r, dict)],
    }


def _fold(text: str) -> str:
    """Case-fold with Turkish diacritics stripped, so ASCII queries
    ("turkiye", "sise") match Turkish names ("TÜRKİYE", "ŞİŞE")."""
    table = str.maketrans({
        "İ": "i", "I": "i", "ı": "i",
        "Ü": "u", "ü": "u", "Ö": "o", "ö": "o",
        "Ç": "c", "ç": "c", "Ş": "s", "ş": "s",
        "Ğ": "g", "ğ": "g",
    })
    return text.translate(table).casefold()


def search_stocks(rows: list[dict], query: str) -> list[dict]:
    """Filter normalised quote rows by symbol or name substring."""
    q = _fold(query.strip())
    if not q:
        return []
    out = []
    for row in rows:
        sym = _fold(str(row.get("symbol") or ""))
        name = _fold(str(row.get("name") or ""))
        if q in sym or q in name:
            out.append(row)
    return out


def parse_chart(payload: dict) -> dict:
    """Normalise a /api/trade/chart payload.

    Returns {"symbol", "current", "points": [{ts, open, high, low,
    close, volume}]} sorted oldest-first. Raises ValueError when
    the API reports no data for the symbol.
    """
    if not payload.get("success"):
        errors = payload.get("errors") or ["no data"]
        raise ValueError("; ".join(str(e) for e in errors))
    data = payload.get("data") or []
    if not data:
        raise ValueError("no data found for the provided symbol")
    entry = data[0]
    points = []
    for p in entry.get("chart") or []:
        points.append({
            "ts": _ts_to_iso(p.get("ts")),
            "open": p.get("o"),
            "high": p.get("h"),
            "low": p.get("l"),
            "close": p.get("c"),
            "volume": p.get("tl"),
        })
    points.sort(key=lambda x: x["ts"] or "")
    return {
        "symbol": entry.get("current", {}).get("s"),
        "current": parse_quote(entry.get("current") or {}),
        "points": points,
        "point_count": len(points),
    }
