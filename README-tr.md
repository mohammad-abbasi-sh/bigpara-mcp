# bigpara-mcp

[Bigpara](https://bigpara.hurriyet.com.tr) (bigpara.hurriyet.com.tr) için resmi olmayan, salt okunur MCP sunucusu — Hürriyet'in finans portalı: canlı BIST hisse fiyatları, TL karşısında döviz kurları, altın fiyatları, BIST endeksleri, kripto ve piyasa hareketleri, ayrıca OHLC fiyat geçmişi.

mcp-name: io.github.mohammad-abbasi-sh/bigpara-mcp

Veriler Bigpara'nın herkese açık JSON API'sinden (`api-bigpara.hurriyet.com.tr`) gelir — giriş gerekmez, API anahtarı gerekmez. Fiyatlar canlı piyasa verisidir; işlem yapmadan önce siteden doğrulayın.

## Yapay zekâ ajanları için

- `bigpara_get_quote(symbols)` — 1–20 sembol için canlı fiyat, örn. `"THYAO,ASELS"` veya `"USDTRY,EURTRY,XU100,GLDGR"`. BIST hisseleri, döviz çiftleri, altın, endeksler, kripto ve emtialar için çalışır. Bilinmeyen semboller `not_found` içinde bildirilir (API onları sessizce atlar).
- `bigpara_search_stocks(query, limit)` — BIST hisselerini sembol veya şirket adıyla bulur, örn. `"thyao"`, `"hava"`, `"banka"`. 661 hisselik evrenin tamamında arar.
- `bigpara_market_movers(market, order, top)` — en çok hareket edenler; `market` `"stocks"` veya `"crypto"`, `order` `"gainers"`, `"losers"` veya `"volume"`.
- `bigpara_gold_prices()` — TL cinsinden 20 altın ürünü: gram, has, çeyrek / yarım / tam / ziynet, gremse, hamit, reşat, 14/18/22 ayar, külçe, ayrıca ons altın (XAUUSD) ve gümüş gram/ons.
- `bigpara_fx_rates()` — TL karşısında 15 döviz çifti: USD, EUR, GBP, CHF, CAD, JPY, CNY, AED, KWD, serbest piyasa AUD, Danimarka/Norveç/İsveç kronu, ruble, riyal.
- `bigpara_price_history(symbol, range, points)` — OHLC fiyat geçmişi; `range` `"daily"` (gün içi, saatlik), `"weekly"`, `"monthly"` veya `"yearly"`.
- `bigpara_health()` — Bigpara API'sine şu anda ulaşılıp ulaşılamadığını kontrol eder.

`bigpara_get_quote` ile sorgulayabileceğiniz başlıca BIST endeksleri: `XU100`, `XU030`, `XBANK`, `XGIDA`, `XHOLD`, `XFINK`, `XSPOR`, `XMADN`, `XELKT`, `XINSA`, `XGMYO`, `XKMYA`, `XHARZ`, `XSBAL`, `XSTKR`, `XUTUM`.

## Kurulum

```bash
uvx bigpara-mcp
```

Veya MCP istemci yapılandırmanıza ekleyin:

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

Python 3.10+ gerektirir.

## Örnekler

```text
THYAO şu an kaç liradan işlem görüyor?
→ bigpara_get_quote("THYAO")

Gram altın fiyatı ne kadar?
→ bigpara_gold_prices()

Bugünün en çok yükselen BIST hisseleri hangileri?
→ bigpara_market_movers("stocks", "gainers", 10)

THYAO'nun son bir aylık fiyatı?
→ bigpara_price_history("THYAO", "monthly", 30)
```

## Notlar

- Salt okunur: sunucu hiçbir şey yazmaz, giriş yapmaz, anahtar istemez.
- Sitenin kendi arama sayfası bir API değildir — sembol araması, trend uç noktasından alınan tam BIST listesini tarar, bu yüzden her zaman günceldir.
- Gerçek zamanlı akış kullanılmaz; fiyatlar ve geçmiş REST API'den gelir.
- `SAUD` döviz sembolü, Bigpara'nın serbest piyasa Avustralya doları için kendi sembolüdür; `SDKK`/`SNOK`/`SRUB`/`SSAR`/`SSEK` serbest piyasa kron/ruble/riyal/krona sembolleridir.
- API, `Symbols` sorgusunu sınırlar; bu yüzden `bigpara_get_quote` çağrı başına en fazla 20 sembol kabul eder.

## Geliştirme

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_markets.py -v   # çevrimdışı, kayıtlı veriler
.venv/bin/python -m pytest tests/test_live.py -v      # canlı, ağ gerektirir
.venv/bin/python tests/smoke_live.py                  # tek nazik yoklama
```

## Lisans

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — kişisel ve ticari olmayan kullanım için ücretsiz; ticari kullanım için ayrı bir lisans gerekir.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
