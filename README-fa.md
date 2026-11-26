# bigpara-mcp

سرور MCP غیررسمی و فقط‌خواندنی برای [Bigpara](https://bigpara.hurriyet.com.tr) (bigpara.hurriyet.com.tr) — پورتال مالی هوریت: قیمت زندهٔ سهام BIST، نرخ ارز در برابر لیر، قیمت طلا، شاخص‌های BIST، کریپتو و تحرکات بازار، به‌علاوهٔ تاریخچهٔ قیمت OHLC.

mcp-name: io.github.mohammad-abbasi-sh/bigpara-mcp

داده‌ها از API عمومی JSON بیگ‌پارا (`api-bigpara.hurriyet.com.tr`) می‌آیند — بدون ورود، بدون کلید API. قیمت‌ها دادهٔ زندهٔ بازارند؛ پیش از هر اقدامی در خود سایت بررسی کنید.

## برای ایجنت‌های هوش مصنوعی

- `bigpara_get_quote(symbols)` — قیمت زنده برای ۱ تا ۲۰ نماد، مثلاً `"THYAO,ASELS"` یا `"USDTRY,EURTRY,XU100,GLDGR"`. برای سهام BIST، جفت‌ارزها، طلا، شاخص‌ها، کریپتو و کالاها کار می‌کند. نمادهای ناشناخته در `not_found` گزارش می‌شوند (API آن‌ها را بی‌صدا حذف می‌کند).
- `bigpara_search_stocks(query, limit)` — یافتن سهام BIST با نماد یا نام شرکت، مثلاً `"thyao"`، `"hava"`، `"banka"`. در کل ۶۶۱ سهم BIST جستجو می‌کند.
- `bigpara_market_movers(market, order, top)` — پرتحرک‌ترین‌ها؛ `market` برابر `"stocks"` یا `"crypto"` و `order` برابر `"gainers"`، `"losers"` یا `"volume"`.
- `bigpara_gold_prices()` — ۲۰ محصول طلا به لیر: گرم، حاس، çeyrek / yarım / tam / ziynet، گرمسه، حامیت، رشاد، عیار ۱۴/۱۸/۲۲، شمش، به‌علاوهٔ اونس طلا (XAUUSD) و نقرهٔ گرم/اونس.
- `bigpara_fx_rates()` — ۱۵ جفت‌ارز در برابر لیر: دلار، یورو، پوند، فرانک، دلار کانادا، ین، یوان، درهم، دینار کویت، دلار استرالیای بازار آزاد، کرون دانمارک/نروژ/سوئد، روبل و ریال.
- `bigpara_price_history(symbol, range, points)` — تاریخچهٔ قیمت OHLC؛ `range` برابر `"daily"` (درون‌روزی، ساعتی)، `"weekly"`، `"monthly"` یا `"yearly"`.
- `bigpara_health()` — بررسی می‌کند که API بیگ‌پارا همین حالا در دسترس است یا نه.

شاخص‌های اصلی BIST که با `bigpara_get_quote` می‌توانید بپرسید: `XU100`، `XU030`، `XBANK`، `XGIDA`، `XHOLD`، `XFINK`، `XSPOR`، `XMADN`، `XELKT`، `XINSA`، `XGMYO`، `XKMYA`، `XHARZ`، `XSBAL`، `XSTKR`، `XUTUM`.

## نصب

```bash
uvx bigpara-mcp
```

یا به پیکربندی کلاینت MCP خود اضافه کنید:

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

نیازمند Python 3.10+.

## نمونه‌ها

```text
THYAO الان چند لیر معامله می‌شود؟
→ bigpara_get_quote("THYAO")

قیمت گرم طلا چقدر است؟
→ bigpara_gold_prices()

پرسودترین سهام BIST امروز کدام‌اند؟
→ bigpara_market_movers("stocks", "gainers", 10)

قیمت THYAO در یک ماه گذشته؟
→ bigpara_price_history("THYAO", "monthly", 30)
```

## نکته‌ها

- فقط‌خواندنی: سرور چیزی نمی‌نویسد، وارد نمی‌شود و کلید نمی‌خواهد.
- صفحهٔ جستجوی خود سایت API نیست — جستجوی نماد، فهرست کامل BIST را از نقطهٔ پایانی ترندها می‌خواند، پس همیشه به‌روز است.
- پخش زنده استفاده نمی‌شود؛ قیمت‌ها و تاریخچه از REST API می‌آیند.
- نماد `SAUD` نماد خود بیگ‌پارا برای دلار استرالیای بازار آزاد است؛ `SDKK`/`SNOK`/`SRUB`/`SSAR`/`SSEK` نمادهای بازار آزاد کرون/روبل/ریال/کرونا هستند.
- API پرس‌وجوی `Symbols` را محدود می‌کند؛ پس `bigpara_get_quote` در هر فراخوانی حداکثر ۲۰ نماد می‌پذیرد.

## توسعه

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_markets.py -v   # آفلاین، با داده‌های ضبط‌شده
.venv/bin/python -m pytest tests/test_live.py -v      # زنده، نیازمند شبکه
.venv/bin/python tests/smoke_live.py                  # یک بررسی ملایم
```

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — برای استفادهٔ شخصی و غیرتجاری رایگان است؛ استفادهٔ تجاری به مجوز جداگانه نیاز دارد.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
