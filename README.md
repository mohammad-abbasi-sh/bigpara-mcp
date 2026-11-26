# bigpara-mcp

Unofficial read-only MCP server for [Bigpara](https://bigpara.hurriyet.com.tr) (bigpara.hurriyet.com.tr) — Hürriyet's finance portal: live BIST stock quotes, FX rates vs TRY, gold prices, BIST indices, crypto and market movers, plus OHLC price history.

mcp-name: io.github.mohammad-abbasi-sh/bigpara-mcp

Data comes from Bigpara's public JSON API (`api-bigpara.hurriyet.com.tr`) — no login, no API key. Prices are live market data; verify on the site before acting on them.

## For AI agents

- `bigpara_get_quote(symbols)` — live quote for 1–20 symbols, e.g. `"THYAO,ASELS"` or `"USDTRY,EURTRY,XU100,GLDGR"`. Works for BIST stocks, FX pairs, gold, indices, crypto and commodities. Unknown symbols are listed in `not_found` (the API silently drops them).
- `bigpara_search_stocks(query, limit)` — find BIST stocks by symbol or company name, e.g. `"thyao"`, `"hava"`, `"banka"`. Searches the full 661-stock universe.
- `bigpara_market_movers(market, order, top)` — top movers; `market` is `"stocks"` or `"crypto"`, `order` is `"gainers"`, `"losers"` or `"volume"`.
- `bigpara_gold_prices()` — 20 gold products in TRY: gram, has, çeyrek / yarım / tam / ziynet, gremse, hamit, reşat, 14/18/22 ayar, külçe, plus ons altın (XAUUSD) and gümüş gram/ons.
- `bigpara_fx_rates()` — 15 FX pairs vs TRY: USD, EUR, GBP, CHF, CAD, JPY, CNY, AED, KWD, free-market AUD, Danish/Norwegian/Swedish krona, ruble, riyal.
- `bigpara_price_history(symbol, range, points)` — OHLC history; `range` is `"daily"` (intraday, hourly), `"weekly"`, `"monthly"` or `"yearly"`.
- `bigpara_health()` — checks whether the Bigpara API is reachable right now.

Major BIST indices you can quote with `bigpara_get_quote`: `XU100`, `XU030`, `XBANK`, `XGIDA`, `XHOLD`, `XFINK`, `XSPOR`, `XMADN`, `XELKT`, `XINSA`, `XGMYO`, `XKMYA`, `XHARZ`, `XSBAL`, `XSTKR`, `XUTUM`.

## Install

```bash
uvx bigpara-mcp
```

Or add to your MCP client config:

```json
{
  "mcpServers": {
    "bigpara": {
      "command": "uvx",
      "args": ["bigpara-mcp"]
    }
  }
}
```

Requires Python 3.10+.

## Examples

```text
What is THYAO trading at right now?
→ bigpara_get_quote("THYAO")

Gram altın fiyatı ne kadar?
→ bigpara_gold_prices()

Biggest BIST gainers today?
→ bigpara_market_movers("stocks", "gainers", 10)

THYAO's price over the last month?
→ bigpara_price_history("THYAO", "monthly", 30)
```

## Notes

- Read-only: the server never writes, logs in, or needs a key.
- The site's own search page is not an API — symbol search scans the full BIST list from the trends endpoint, so it is always current.
- Real-time streaming is not used; quotes and history come from the REST API.
- FX symbol `SAUD` is Bigpara's own symbol for the free-market Australian dollar; `SDKK`/`SNOK`/`SRUB`/`SSAR`/`SSEK` are its free-market krone/ruble/riyal/krona symbols.
- The API caps the `Symbols` query, so `bigpara_get_quote` accepts at most 20 symbols per call.

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_markets.py -v   # offline, recorded fixtures
.venv/bin/python -m pytest tests/test_live.py -v      # live, needs network
.venv/bin/python tests/smoke_live.py                  # one polite probe
```

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — free for personal and non-commercial use; commercial use needs a separate license.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
