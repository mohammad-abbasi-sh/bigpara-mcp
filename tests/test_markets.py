"""Offline tests for bigpara_mcp.markets — recorded real Bigpara API
responses (api-bigpara.hurriyet.com.tr, fetched 2026-11-26, plain
curl, browser UA):

- current-mixed.json: /api/trade/current?Symbols=USDTRY,EURTRY,XU100,
  THYAO,ASELS (5 rows; USDTRY 50.6771, XU100 10864.68).
- current-gold.json: the 20 GOLD_SYMBOLS (GLDGR gram altın ~5820 TL,
  SGLDC çeyrek ~10140 TL, XAUUSD ons ~3570 USD — live prices, tests
  assert ranges, not exact values).
- current-fx.json: 17 FX rows (USDTRY, EURTRY, GBPTRY, ... SSAR).
- current-unknown-symbol.json: Symbols=XXXXZZZ,thyao — the API
  silently drops the unknown symbol (success stays true, errors []),
  only THYAO comes back.
- trends-gainers.json / trends-losers.json / trends-volume.json:
  /api/trade/trends Top=5 (totalCount 661; first gainer FZLGY,
  first loser DOGUB, most-traded SASA).
- crypto-trends-gainers.json: /api/crypto/trends Top=5
  (totalCount 395; first BLURTRY:BNN).
- chart-daily-thyao.json: /api/trade/chart/daily/1h/last/24 (24 pts).
- chart-monthly-thyao.json: /api/trade/chart/monthly/1d/last/30
  (22 pts — trading days only).
- chart-yearly-xu100.json: /api/trade/chart/yearly/1d/last/365
  (248 pts).
"""
import json
import os
import unittest

from bigpara_mcp import markets as M

FIX = os.path.join(os.path.dirname(__file__), "fixtures")


def _load(name: str) -> dict:
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return json.load(f)


class TestParseQuote(unittest.TestCase):
    def test_mixed(self):
        out = M.parse_quotes(_load("current-mixed.json"),
                             ["USDTRY", "EURTRY", "XU100", "THYAO", "ASELS"])
        self.assertEqual(out["count"], 5)
        self.assertEqual(out["not_found"], [])
        usd = next(q for q in out["quotes"] if q["symbol"] == "USDTRY")
        self.assertEqual(usd["name"], "Amerikan Doları Türk Lirası")
        self.assertEqual(usd["price"], 50.6771)
        self.assertEqual(usd["market"], "Currency")
        self.assertTrue(usd["as_of"].endswith("+00:00"))
        self.assertEqual(usd["url"],
                         "https://bigpara.hurriyet.com.tr/doviz/dolar/")
        xu = next(q for q in out["quotes"] if q["symbol"] == "XU100")
        self.assertEqual(xu["name"], "BIST 100")
        self.assertEqual(xu["market"], "Index")
        self.assertAlmostEqual(xu["change_pct"], 1.83)

    def test_unknown_symbol_reported(self):
        out = M.parse_quotes(_load("current-unknown-symbol.json"),
                             ["XXXXZZZ", "THYAO"])
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["quotes"][0]["symbol"], "THYAO")
        self.assertEqual(out["not_found"], ["XXXXZZZ"])

    def test_gold(self):
        out = M.parse_quotes(_load("current-gold.json"), M.GOLD_SYMBOLS)
        self.assertEqual(out["count"], 20)
        self.assertEqual(out["not_found"], [])
        gram = next(q for q in out["quotes"] if q["symbol"] == "GLDGR")
        self.assertEqual(gram["name"], "ALTIN GRAM - TL")
        self.assertGreater(gram["price"], 5000)  # live price; range only
        self.assertLess(gram["price"], 7000)
        ceyrek = next(q for q in out["quotes"] if q["symbol"] == "SGLDC")
        self.assertEqual(ceyrek["name"], "Ceyrek Altin")
        self.assertGreater(ceyrek["price"], 9000)
        self.assertLess(ceyrek["price"], 12000)
        gumus = next(q for q in out["quotes"] if q["symbol"] == "SXAGGR")
        self.assertEqual(gumus["name"], "Gumus Gram")

    def test_fx(self):
        out = M.parse_quotes(_load("current-fx.json"), M.FX_SYMBOLS)
        # FX list has 15 symbols; the fixture also carries XAUUSD/XAGUSD
        self.assertEqual(out["count"], 17)
        self.assertEqual(out["not_found"], [])
        eur = next(q for q in out["quotes"] if q["symbol"] == "EURTRY")
        self.assertEqual(eur["price"], 55.7905)
        self.assertEqual(eur["name"], "Euro Türk Lirası")


class TestParseTrends(unittest.TestCase):
    def test_gainers(self):
        out = M.parse_trends(_load("trends-gainers.json"))
        self.assertEqual(out["total"], 661)
        self.assertEqual(out["count"], 5)
        first = out["items"][0]
        self.assertEqual(first["symbol"], "FZLGY")
        self.assertEqual(first["name"], "FUZUL GMYO")
        self.assertEqual(first["change_pct"], 10)
        self.assertEqual(first["market"], None)  # trends rows lack ms

    def test_losers_descending_negative(self):
        out = M.parse_trends(_load("trends-losers.json"))
        self.assertEqual(out["items"][0]["symbol"], "DOGUB")
        for item in out["items"]:
            self.assertLess(item["change_pct"], 0)

    def test_volume(self):
        out = M.parse_trends(_load("trends-volume.json"))
        self.assertEqual(out["items"][0]["symbol"], "SASA")
        self.assertGreater(out["items"][0]["volume"], 0)

    def test_crypto(self):
        out = M.parse_trends(_load("crypto-trends-gainers.json"))
        self.assertEqual(out["total"], 395)
        first = out["items"][0]
        self.assertEqual(first["symbol"], "BLURTRY:BNN")
        self.assertEqual(first["market"], "Cryptocurrency")


class TestSearchStocks(unittest.TestCase):
    def _rows(self):
        return M.parse_trends(_load("trends-volume.json"))["items"]

    def test_by_symbol(self):
        hits = M.search_stocks(self._rows(), "sasa")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["symbol"], "SASA")

    def test_by_name_case_insensitive(self):
        hits = M.search_stocks(self._rows(), "POLYESTER")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["symbol"], "SASA")

    def test_turkish_fold(self):
        # ASCII queries must match Turkish names: "turkiye" and
        # "türkiye" both find "TÜRKİYE SİGORTA".
        rows = [{"symbol": "TURSG", "name": "TÜRKİYE SİGORTA"}]
        self.assertEqual(len(M.search_stocks(rows, "türkiye")), 1)
        self.assertEqual(len(M.search_stocks(rows, "turkiye")), 1)
        self.assertEqual(len(M.search_stocks(rows, "TURKIYE")), 1)

    def test_no_match_and_empty(self):
        self.assertEqual(M.search_stocks(self._rows(), "zzzzqq"), [])
        self.assertEqual(M.search_stocks(self._rows(), "  "), [])


class TestParseChart(unittest.TestCase):
    def test_daily(self):
        out = M.parse_chart(_load("chart-daily-thyao.json"))
        self.assertEqual(out["symbol"], "THYAO")
        self.assertEqual(out["point_count"], 24)
        self.assertEqual(out["current"]["symbol"], "THYAO")
        self.assertEqual(out["current"]["price"], 311.75)
        first, last = out["points"][0], out["points"][-1]
        self.assertLessEqual(first["ts"], last["ts"])  # oldest first
        for p in out["points"]:
            self.assertLessEqual(p["low"], p["high"])
            self.assertTrue(p["ts"].endswith("+00:00"))

    def test_monthly(self):
        out = M.parse_chart(_load("chart-monthly-thyao.json"))
        self.assertEqual(out["point_count"], 22)
        self.assertEqual(out["symbol"], "THYAO")

    def test_yearly_index(self):
        out = M.parse_chart(_load("chart-yearly-xu100.json"))
        self.assertEqual(out["symbol"], "XU100")
        self.assertEqual(out["point_count"], 248)
        self.assertEqual(out["current"]["market"], "Index")

    def test_no_data_raises(self):
        with self.assertRaises(ValueError):
            M.parse_chart({"data": [], "errors":
                           ["No data found for the provided symbols."],
                           "success": False})


class TestConstants(unittest.TestCase):
    def test_symbol_lists(self):
        self.assertEqual(len(M.GOLD_SYMBOLS), 20)
        self.assertEqual(len(M.FX_SYMBOLS), 15)
        self.assertLessEqual(len(M.GOLD_SYMBOLS),
                             M.MAX_SYMBOLS_PER_CALL)
        self.assertLessEqual(len(M.FX_SYMBOLS),
                             M.MAX_SYMBOLS_PER_CALL)
        self.assertEqual(set(M.CHART_RANGES),
                         {"daily", "weekly", "monthly", "yearly"})


if __name__ == "__main__":
    unittest.main()
