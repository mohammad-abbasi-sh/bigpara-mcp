"""Live tests for bigpara_mcp — real requests to
api-bigpara.hurriyet.com.tr.

Requires network + Chrome TLS impersonation (curl-cffi). The server
is polite by design (~0.8s between requests), so this file takes
~20s. Run: python -m pytest tests/test_live.py -v

Prices move during the day; tests assert structure and sane ranges,
not exact values.
"""
import unittest

from bigpara_mcp import http as H
from bigpara_mcp import markets as M


class TestLiveCurrent(unittest.TestCase):
    def test_mixed(self):
        payload = H.fetch_current(["USDTRY", "EURTRY", "XU100",
                                   "THYAO", "GLDGR"])
        out = M.parse_quotes(payload, ["USDTRY", "EURTRY", "XU100",
                                       "THYAO", "GLDGR"])
        self.assertEqual(out["count"], 5)
        self.assertEqual(out["not_found"], [])
        usd = next(q for q in out["quotes"] if q["symbol"] == "USDTRY")
        self.assertGreater(usd["price"], 40)
        self.assertLess(usd["price"], 70)
        xu = next(q for q in out["quotes"] if q["symbol"] == "XU100")
        self.assertGreater(xu["price"], 5000)
        gram = next(q for q in out["quotes"] if q["symbol"] == "GLDGR")
        self.assertGreater(gram["price"], 1000)

    def test_unknown_symbol_dropped(self):
        payload = H.fetch_current(["XXXXZZZ", "THYAO"])
        out = M.parse_quotes(payload, ["XXXXZZZ", "THYAO"])
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["not_found"], ["XXXXZZZ"])

    def test_gold_list(self):
        payload = H.fetch_current(M.GOLD_SYMBOLS)
        out = M.parse_quotes(payload, M.GOLD_SYMBOLS)
        self.assertEqual(out["count"], 20)
        self.assertEqual(out["not_found"], [])

    def test_fx_list(self):
        payload = H.fetch_current(M.FX_SYMBOLS)
        out = M.parse_quotes(payload, M.FX_SYMBOLS)
        self.assertEqual(out["count"], 15)
        self.assertEqual(out["not_found"], [])

    def test_indices(self):
        payload = H.fetch_current(M.INDEX_SYMBOLS)
        out = M.parse_quotes(payload, M.INDEX_SYMBOLS)
        self.assertEqual(out["count"], len(M.INDEX_SYMBOLS))
        self.assertEqual(out["not_found"], [])


class TestLiveTrends(unittest.TestCase):
    def test_gainers(self):
        payload = H.fetch_trends("pdesc", 5)
        out = M.parse_trends(payload)
        self.assertEqual(out["count"], 5)
        self.assertGreaterEqual(out["total"], 600)
        self.assertGreater(out["items"][0]["change_pct"], 0)

    def test_losers(self):
        payload = H.fetch_trends("pasc", 5)
        out = M.parse_trends(payload)
        self.assertEqual(out["count"], 5)
        self.assertLess(out["items"][0]["change_pct"], 0)

    def test_volume(self):
        payload = H.fetch_trends("tv", 5)
        out = M.parse_trends(payload)
        self.assertEqual(out["count"], 5)
        self.assertGreater(out["items"][0]["volume"], 0)

    def test_crypto(self):
        payload = H.fetch_trends("pdesc", 5, crypto=True)
        out = M.parse_trends(payload)
        self.assertEqual(out["count"], 5)
        self.assertGreaterEqual(out["total"], 300)
        self.assertEqual(out["items"][0]["market"], "Cryptocurrency")

    def test_universe_count(self):
        payload = H.fetch_trends("tv", M.STOCK_UNIVERSE_TOP)
        out = M.parse_trends(payload)
        self.assertEqual(out["count"], out["total"])
        self.assertGreaterEqual(out["total"], 600)


class TestLiveChart(unittest.TestCase):
    def test_daily(self):
        payload = H.fetch_chart("THYAO", "daily", "1h", 24)
        out = M.parse_chart(payload)
        self.assertEqual(out["symbol"], "THYAO")
        self.assertGreater(out["point_count"], 0)
        self.assertLessEqual(out["point_count"], 24)

    def test_monthly(self):
        payload = H.fetch_chart("THYAO", "monthly", "1d", 30)
        out = M.parse_chart(payload)
        self.assertEqual(out["symbol"], "THYAO")
        self.assertGreater(out["point_count"], 10)

    def test_yearly_index(self):
        payload = H.fetch_chart("XU100", "yearly", "1d", 365)
        out = M.parse_chart(payload)
        self.assertEqual(out["symbol"], "XU100")
        self.assertGreater(out["point_count"], 100)

    def test_unknown_symbol(self):
        payload = H.fetch_chart("XXXXZZZ", "daily", "1h", 24)
        with self.assertRaises(ValueError):
            M.parse_chart(payload)


class TestLiveSearch(unittest.TestCase):
    def test_search_thyao(self):
        payload = H.fetch_trends("tv", M.STOCK_UNIVERSE_TOP)
        rows = M.parse_trends(payload)["items"]
        hits = M.search_stocks(rows, "thyao")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["symbol"], "THYAO")

    def test_search_banka(self):
        payload = H.fetch_trends("tv", M.STOCK_UNIVERSE_TOP)
        rows = M.parse_trends(payload)["items"]
        hits = M.search_stocks(rows, "banka")
        self.assertGreater(len(hits), 5)


class TestLiveHealth(unittest.TestCase):
    def test_health_ok(self):
        result = H.health_check()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["http_status"], 200)


if __name__ == "__main__":
    unittest.main()
