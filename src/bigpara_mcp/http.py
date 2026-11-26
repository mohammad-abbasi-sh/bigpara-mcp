"""HTTP layer for bigpara_mcp.

Bigpara (bigpara.hurriyet.com.tr) is Hürriyet's finance portal. Its
pages are server-rendered, but the live market data comes from a public
JSON API at api-bigpara.hurriyet.com.tr — no login, no API key, no
session cookies needed. Plain curl answers HTTP 200 (verified live
2026-11-26); the transport still uses curl-cffi Chrome impersonation,
the same proven pattern as the other Turkey-factory servers, in case
the posture tightens. Requests are kept gentle (one at a time,
~0.8s apart) and read-only.

Endpoints used (all GET, api-bigpara.hurriyet.com.tr):
  /api/trade/current?Symbols=A,B,C   live quote for any symbol
    (BIST stocks, FX, gold, indices, crypto, commodities). Unknown
    symbols are silently dropped from `data`; lowercase input is
    accepted and normalised. A Symbols value that is too long
    returns HTTP 400 "Each symbol must be 25 characters or less"
    — callers cap the list at 20 symbols.
  /api/trade/trends?Order=pasc|pdesc|tv&Top=N
    BIST movers: pasc = biggest losers, pdesc = biggest gainers,
    tv = most traded by volume. Top=700 returns the whole
    661-stock universe (totalCount 661).
  /api/crypto/trends?Order=pasc|pdesc|tv&Top=N
    same for crypto (totalCount 395).
  /api/trade/chart/{range}/{res}/last/{n}?symbols=S
    OHLC history; ranges: daily/1h/24, weekly/1d/7,
    monthly/1d/30, yearly/1d/365 (verified live 2026-11-26).

Caveats found while probing (2026-11-26): the site's own search
(/arama/?s=) is a server-rendered page, not an API — symbol search
here scans the full 661-stock list from the trends endpoint.
Real-time streaming (realtime-bigpara.hurriyet.com.tr/tradehub)
is not used; the REST API is enough for quotes and history.
"""
from __future__ import annotations

import time

from curl_cffi import requests as _r

API_BASE = "https://api-bigpara.hurriyet.com.tr"
SITE_BASE = "https://bigpara.hurriyet.com.tr"
TIMEOUT = 30.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

_last_fetch = 0.0


class BigparaError(RuntimeError):
    pass


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, params: dict | None = None) -> dict:
    """GET JSON with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process),
    retries once with the next profile on HTTP 403/429 or a
    transport error. Enforces MIN_INTERVAL between requests.
    Returns the parsed JSON body (dict). Raises BigparaError.
    """
    global _last_fetch, _profile_idx
    last_exc: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + attempt) % len(_PROFILES)]
        wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
        if wait > 0:
            time.sleep(wait)
        try:
            resp = _r.get(url, params=params, headers=_HEADERS,
                          impersonate=profile, timeout=TIMEOUT)
            _last_fetch = time.monotonic()
        except Exception as e:  # transport error (RST, timeout, ...)
            last_exc = e
            time.sleep(_RETRY_BACKOFF)
            continue
        if resp.status_code in (403, 429):
            last_exc = BigparaError(
                f"Bigpara returned HTTP {resp.status_code} for {url}")
            time.sleep(_RETRY_BACKOFF)
            continue
        if resp.status_code != 200:
            raise BigparaError(
                f"Bigpara returned HTTP {resp.status_code} for {url}")
        _profile_idx = (_profile_idx + attempt) % len(_PROFILES)
        try:
            data = resp.json()
        except ValueError as e:
            raise BigparaError(
                f"Bigpara returned non-JSON for {url}") from e
        if not isinstance(data, dict):
            raise BigparaError(
                f"Bigpara returned unexpected JSON for {url}")
        return data
    raise BigparaError(
        f"Bigpara unreachable for {url}: {last_exc}") from last_exc


def fetch_current(symbols: list[str]) -> dict:
    """Live quotes for 1-20 symbols (comma-joined, upper-cased)."""
    return _request(f"{API_BASE}/api/trade/current",
                    params={"Symbols": ",".join(symbols)})


def fetch_trends(order: str, top: int, crypto: bool = False) -> dict:
    """Movers list. order: pasc (losers) | pdesc (gainers) | tv (volume)."""
    path = "/api/crypto/trends" if crypto else "/api/trade/trends"
    return _request(f"{API_BASE}{path}",
                    params={"Order": order, "Top": top})


def fetch_chart(symbol: str, range_: str, resolution: str,
                points: int) -> dict:
    """OHLC history for one symbol."""
    return _request(
        f"{API_BASE}/api/trade/chart/{range_}/{resolution}/last/{points}",
        params={"symbols": symbol})


def health_check() -> dict:
    """One polite probe of the API.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `bigpara_health` tool
    and the daily smoke CI.
    """
    url = f"{API_BASE}/api/trade/current?Symbols=USDTRY"
    try:
        fetch_current(["USDTRY"])
    except BigparaError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403,
                    "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429,
                    "url": url, "detail": msg}
        return {"status": "error", "http_status": None,
                "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
