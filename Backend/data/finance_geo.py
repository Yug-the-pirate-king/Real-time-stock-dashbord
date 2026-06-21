"""
Finance geography data extracted from World Monitor (finance variant).
Contains stock exchanges, central banks, and RSS feed maps.
"""

STOCK_EXCHANGES = [
    {"id": "nyse", "name": "New York Stock Exchange", "shortName": "NYSE", "city": "New York", "country": "US", "lat": 40.7069, "lon": -74.0113, "tier": "mega", "marketCap": 28.0, "tradingHours": "09:30-16:00 ET", "timezone": "America/New_York", "description": "Largest stock exchange by market cap"},
    {"id": "nasdaq", "name": "NASDAQ", "shortName": "NASDAQ", "city": "New York", "country": "US", "lat": 40.7568, "lon": -73.9860, "tier": "mega", "marketCap": 24.0, "tradingHours": "09:30-16:00 ET", "timezone": "America/New_York", "description": "Tech-heavy electronic exchange"},
    {"id": "sse", "name": "Shanghai Stock Exchange", "shortName": "SSE", "city": "Shanghai", "country": "CN", "lat": 31.2333, "lon": 121.4865, "tier": "mega", "marketCap": 7.4, "tradingHours": "09:30-15:00 CST", "timezone": "Asia/Shanghai", "description": "Largest exchange in China"},
    {"id": "euronext", "name": "Euronext", "shortName": "Euronext", "city": "Amsterdam", "country": "NL", "lat": 52.3465, "lon": 4.8790, "tier": "mega", "marketCap": 7.2, "tradingHours": "09:00-17:30 CET", "timezone": "Europe/Amsterdam", "description": "Pan-European exchange"},
    {"id": "jpx", "name": "Japan Exchange Group", "shortName": "JPX/TSE", "city": "Tokyo", "country": "JP", "lat": 35.6803, "lon": 139.7717, "tier": "mega", "marketCap": 6.5, "tradingHours": "09:00-15:00 JST", "timezone": "Asia/Tokyo", "description": "Tokyo Stock Exchange"},
    {"id": "szse", "name": "Shenzhen Stock Exchange", "shortName": "SZSE", "city": "Shenzhen", "country": "CN", "lat": 22.5367, "lon": 114.0571, "tier": "major", "marketCap": 4.8, "tradingHours": "09:30-15:00 CST", "timezone": "Asia/Shanghai", "description": "Tech-oriented Chinese exchange"},
    {"id": "hkex", "name": "Hong Kong Stock Exchange", "shortName": "HKEX", "city": "Hong Kong", "country": "HK", "lat": 22.2832, "lon": 114.1569, "tier": "major", "marketCap": 4.5, "tradingHours": "09:30-16:00 HKT", "timezone": "Asia/Hong_Kong", "description": "Gateway to Chinese markets"},
    {"id": "lse", "name": "London Stock Exchange", "shortName": "LSE", "city": "London", "country": "GB", "lat": 51.5155, "lon": -0.0922, "tier": "major", "marketCap": 3.4, "tradingHours": "08:00-16:30 GMT", "timezone": "Europe/London", "description": "Europe's largest exchange"},
    {"id": "nse-india", "name": "National Stock Exchange of India", "shortName": "NSE", "city": "Mumbai", "country": "IN", "lat": 19.0557, "lon": 72.8525, "tier": "major", "marketCap": 3.6, "tradingHours": "09:15-15:30 IST", "timezone": "Asia/Kolkata", "description": "India's largest exchange by volume"},
    {"id": "bse-india", "name": "BSE (Bombay Stock Exchange)", "shortName": "BSE", "city": "Mumbai", "country": "IN", "lat": 18.9281, "lon": 72.8333, "tier": "major", "marketCap": 3.4, "tradingHours": "09:15-15:30 IST", "timezone": "Asia/Kolkata", "description": "Asia's oldest exchange"},
    {"id": "tsx", "name": "Toronto Stock Exchange", "shortName": "TSX", "city": "Toronto", "country": "CA", "lat": 43.6489, "lon": -79.3818, "tier": "major", "marketCap": 2.8, "tradingHours": "09:30-16:00 ET", "timezone": "America/Toronto", "description": "Canada's largest exchange"},
    {"id": "krx", "name": "Korea Exchange", "shortName": "KRX", "city": "Seoul", "country": "KR", "lat": 37.5230, "lon": 126.9258, "tier": "major", "marketCap": 2.2, "tradingHours": "09:00-15:30 KST", "timezone": "Asia/Seoul", "description": "South Korea's exchange"},
    {"id": "six", "name": "SIX Swiss Exchange", "shortName": "SIX", "city": "Zurich", "country": "CH", "lat": 47.3685, "lon": 8.5400, "tier": "major", "marketCap": 2.0, "tradingHours": "09:00-17:30 CET", "timezone": "Europe/Zurich", "description": "Switzerland's primary exchange"},
    {"id": "asx", "name": "Australian Securities Exchange", "shortName": "ASX", "city": "Sydney", "country": "AU", "lat": -33.8672, "lon": 151.2067, "tier": "major", "marketCap": 1.7, "tradingHours": "10:00-16:00 AEST", "timezone": "Australia/Sydney", "description": "Australia's primary exchange"},
    {"id": "xetra", "name": "Deutsche Börse (Xetra)", "shortName": "Xetra", "city": "Frankfurt", "country": "DE", "lat": 50.1110, "lon": 8.6804, "tier": "major", "marketCap": 2.3, "tradingHours": "09:00-17:30 CET", "timezone": "Europe/Berlin", "description": "Germany's primary exchange"},
    {"id": "twse", "name": "Taiwan Stock Exchange", "shortName": "TWSE", "city": "Taipei", "country": "TW", "lat": 25.0388, "lon": 121.5632, "tier": "major", "marketCap": 2.0, "tradingHours": "09:00-13:30 CST", "timezone": "Asia/Taipei", "description": "Taiwan's primary exchange"},
    {"id": "b3", "name": "B3 (Brasil Bolsa Balcão)", "shortName": "B3", "city": "São Paulo", "country": "BR", "lat": -23.5486, "lon": -46.6341, "tier": "emerging", "marketCap": 0.9, "tradingHours": "10:00-17:30 BRT", "timezone": "America/Sao_Paulo", "description": "Brazil's stock exchange"},
    {"id": "jse", "name": "Johannesburg Stock Exchange", "shortName": "JSE", "city": "Johannesburg", "country": "ZA", "lat": -26.1088, "lon": 28.0318, "tier": "emerging", "marketCap": 1.2, "tradingHours": "09:00-17:00 SAST", "timezone": "Africa/Johannesburg", "description": "Africa's largest exchange"},
    {"id": "sgx", "name": "Singapore Exchange", "shortName": "SGX", "city": "Singapore", "country": "SG", "lat": 1.2794, "lon": 103.8498, "tier": "major", "marketCap": 0.7, "tradingHours": "09:00-17:00 SGT", "timezone": "Asia/Singapore", "description": "Singapore's exchange"},
    {"id": "tadawul", "name": "Saudi Exchange (Tadawul)", "shortName": "Tadawul", "city": "Riyadh", "country": "SA", "lat": 24.7103, "lon": 46.6770, "tier": "emerging", "marketCap": 2.9, "tradingHours": "10:00-15:00 AST", "timezone": "Asia/Riyadh", "description": "Saudi Arabia's exchange"},
    {"id": "idx", "name": "Indonesia Stock Exchange", "shortName": "IDX", "city": "Jakarta", "country": "ID", "lat": -6.2293, "lon": 106.8130, "tier": "emerging", "marketCap": 0.6, "tradingHours": "09:00-15:50 WIB", "timezone": "Asia/Jakarta", "description": "Indonesia's primary exchange"},
    {"id": "set", "name": "Stock Exchange of Thailand", "shortName": "SET", "city": "Bangkok", "country": "TH", "lat": 13.7205, "lon": 100.5250, "tier": "emerging", "marketCap": 0.5, "tradingHours": "10:00-16:30 ICT", "timezone": "Asia/Bangkok", "description": "Thailand's exchange"},
    {"id": "bvl", "name": "Bolsa de Valores de Lima", "shortName": "BVL", "city": "Lima", "country": "PE", "lat": -12.0483, "lon": -77.0258, "tier": "emerging", "description": "Peru's stock exchange"},
    {"id": "bmv", "name": "Bolsa Mexicana de Valores", "shortName": "BMV", "city": "Mexico City", "country": "MX", "lat": 19.4345, "lon": -99.1424, "tier": "emerging", "marketCap": 0.5, "tradingHours": "08:30-15:00 CT", "timezone": "America/Mexico_City", "description": "Mexico's stock exchange"},
    {"id": "moex", "name": "Moscow Exchange", "shortName": "MOEX", "city": "Moscow", "country": "RU", "lat": 55.7539, "lon": 37.6084, "tier": "emerging", "marketCap": 0.6, "tradingHours": "09:50-18:50 MSK", "timezone": "Europe/Moscow", "description": "Russia's largest exchange"},
    {"id": "nse-nig", "name": "Nigerian Exchange", "shortName": "NGX", "city": "Lagos", "country": "NG", "lat": 6.4549, "lon": 3.4246, "tier": "emerging", "description": "Nigeria's exchange"},
    {"id": "egx", "name": "Egyptian Exchange", "shortName": "EGX", "city": "Cairo", "country": "EG", "lat": 30.0492, "lon": 31.2340, "tier": "emerging", "description": "Egypt's exchange"},
    {"id": "nzx", "name": "New Zealand Exchange", "shortName": "NZX", "city": "Wellington", "country": "NZ", "lat": -41.2866, "lon": 174.7756, "tier": "emerging", "description": "New Zealand's exchange"},
    {"id": "tase", "name": "Tel Aviv Stock Exchange", "shortName": "TASE", "city": "Tel Aviv", "country": "IL", "lat": 32.0669, "lon": 34.7856, "tier": "emerging", "marketCap": 0.3, "tradingHours": "09:59-17:15 IST", "timezone": "Asia/Jerusalem", "description": "Israel's exchange"},
]

CENTRAL_BANKS = [
    {"id": "fed", "name": "Federal Reserve", "shortName": "Fed", "city": "Washington D.C.", "country": "US", "lat": 38.8928, "lon": -77.0455, "type": "major", "currency": "USD", "description": "US central bank, global reserve currency issuer"},
    {"id": "ecb", "name": "European Central Bank", "shortName": "ECB", "city": "Frankfurt", "country": "DE", "lat": 50.1096, "lon": 8.7033, "type": "supranational", "currency": "EUR", "description": "Eurozone monetary authority"},
    {"id": "boj", "name": "Bank of Japan", "shortName": "BoJ", "city": "Tokyo", "country": "JP", "lat": 35.6867, "lon": 139.7635, "type": "major", "currency": "JPY", "description": "Japan's central bank"},
    {"id": "boe", "name": "Bank of England", "shortName": "BoE", "city": "London", "country": "GB", "lat": 51.5142, "lon": -0.0882, "type": "major", "currency": "GBP", "description": "UK's central bank"},
    {"id": "pboc", "name": "People's Bank of China", "shortName": "PBoC", "city": "Beijing", "country": "CN", "lat": 39.9064, "lon": 116.4038, "type": "major", "currency": "CNY", "description": "China's central bank"},
    {"id": "snb", "name": "Swiss National Bank", "shortName": "SNB", "city": "Bern", "country": "CH", "lat": 46.9482, "lon": 7.4476, "type": "major", "currency": "CHF", "description": "Switzerland's central bank"},
    {"id": "rba", "name": "Reserve Bank of Australia", "shortName": "RBA", "city": "Sydney", "country": "AU", "lat": -33.8627, "lon": 151.2111, "type": "major", "currency": "AUD", "description": "Australia's central bank"},
    {"id": "boc", "name": "Bank of Canada", "shortName": "BoC", "city": "Ottawa", "country": "CA", "lat": 45.4230, "lon": -75.7010, "type": "major", "currency": "CAD", "description": "Canada's central bank"},
    {"id": "rbi", "name": "Reserve Bank of India", "shortName": "RBI", "city": "Mumbai", "country": "IN", "lat": 18.9323, "lon": 72.8338, "type": "major", "currency": "INR", "description": "India's central bank"},
    {"id": "bok", "name": "Bank of Korea", "shortName": "BoK", "city": "Seoul", "country": "KR", "lat": 37.5604, "lon": 126.9814, "type": "major", "currency": "KRW", "description": "South Korea's central bank"},
    {"id": "bcb", "name": "Banco Central do Brasil", "shortName": "BCB", "city": "Brasília", "country": "BR", "lat": -15.7839, "lon": -47.8829, "type": "regional", "currency": "BRL", "description": "Brazil's central bank"},
    {"id": "sama", "name": "Saudi Central Bank", "shortName": "SAMA", "city": "Riyadh", "country": "SA", "lat": 24.6938, "lon": 46.6850, "type": "regional", "currency": "SAR", "description": "Saudi Arabia's central bank"},
    {"id": "bis", "name": "Bank for International Settlements", "shortName": "BIS", "city": "Basel", "country": "CH", "lat": 47.5585, "lon": 7.5866, "type": "supranational", "description": "Central bank of central banks"},
    {"id": "imf", "name": "International Monetary Fund", "shortName": "IMF", "city": "Washington D.C.", "country": "US", "lat": 38.8987, "lon": -77.0425, "type": "supranational", "description": "Global financial stability institution"},
]

# Finance-focused RSS feed map (derived from World Monitor finance variant)
FEEDS = {
    "markets": [
        {"name": "CNBC", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
        {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/rss/topstories"},
        {"name": "Seeking Alpha", "url": "https://seekingalpha.com/market_currents.xml"},
    ],
    "forex": [
        {"name": "Forex News", "url": "https://news.google.com/rss/search?q=(forex+OR+currency+OR+FX+market)+trading+when:1d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Dollar Watch", "url": "https://news.google.com/rss/search?q=(dollar+index+OR+DXY+OR+US+dollar+OR+euro+dollar)+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Central Bank Rates", "url": "https://news.google.com/rss/search?q=(central+bank+OR+interest+rate+OR+rate+decision+OR+monetary+policy)+when:2d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "bonds": [
        {"name": "Bond Market", "url": "https://news.google.com/rss/search?q=(bond+market+OR+treasury+yields+OR+bond+yields+OR+fixed+income)+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Treasury Watch", "url": "https://news.google.com/rss/search?q=(US+Treasury+OR+Treasury+auction+OR+10-year+yield+OR+2-year+yield)+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Corporate Bonds", "url": "https://news.google.com/rss/search?q=(corporate+bond+OR+high+yield+OR+investment+grade+OR+credit+spread)+when:3d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "commodities": [
        {"name": "Oil & Gas", "url": "https://news.google.com/rss/search?q=(oil+price+OR+OPEC+OR+natural+gas+OR+crude+oil+OR+WTI+OR+Brent)+when:1d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Gold & Metals", "url": "https://news.google.com/rss/search?q=(gold+price+OR+silver+price+OR+copper+OR+platinum+OR+precious+metals)+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Agriculture", "url": "https://news.google.com/rss/search?q=(wheat+OR+corn+OR+soybeans+OR+coffee+OR+sugar)+price+OR+commodity+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Commodity Trading", "url": "https://news.google.com/rss/search?q=(commodity+trading+OR+futures+market+OR+CME+OR+NYMEX+OR+COMEX)+when:2d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "crypto": [
        {"name": "CoinDesk", "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
        {"name": "Cointelegraph", "url": "https://cointelegraph.com/rss"},
        {"name": "Crypto News", "url": "https://news.google.com/rss/search?q=(bitcoin+OR+ethereum+OR+crypto+OR+digital+assets)+when:1d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "DeFi News", "url": "https://news.google.com/rss/search?q=(DeFi+OR+decentralized+finance+OR+DEX+OR+yield+farming)+when:3d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "centralbanks": [
        {"name": "Federal Reserve", "url": "https://www.federalreserve.gov/feeds/press_all.xml"},
        {"name": "ECB Watch", "url": "https://news.google.com/rss/search?q=(European+Central+Bank+OR+ECB+OR+Lagarde)+monetary+policy+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "BoJ Watch", "url": "https://news.google.com/rss/search?q=(Bank+of+Japan+OR+BoJ)+monetary+policy+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "BoE Watch", "url": "https://news.google.com/rss/search?q=(Bank+of+England+OR+BoE)+monetary+policy+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Global Central Banks", "url": "https://news.google.com/rss/search?q=(rate+hike+OR+rate+cut+OR+interest+rate+decision)+central+bank+when:3d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "economic": [
        {"name": "Economic Data", "url": "https://news.google.com/rss/search?q=(CPI+OR+inflation+OR+GDP+OR+jobs+report+OR+nonfarm+payrolls+OR+PMI)+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Trade & Tariffs", "url": "https://news.google.com/rss/search?q=(tariff+OR+trade+war+OR+trade+deficit+OR+sanctions)+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Housing Market", "url": "https://news.google.com/rss/search?q=(housing+market+OR+home+prices+OR+mortgage+rates+OR+REIT)+when:3d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "ipo": [
        {"name": "IPO News", "url": "https://news.google.com/rss/search?q=(IPO+OR+initial+public+offering+OR+SPAC+OR+direct+listing)+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Earnings Reports", "url": "https://news.google.com/rss/search?q=(earnings+report+OR+quarterly+earnings+OR+revenue+beat+OR+earnings+miss)+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "M&A News", "url": "https://news.google.com/rss/search?q=(merger+OR+acquisition+OR+takeover+bid+OR+buyout)+billion+when:3d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "derivatives": [
        {"name": "Options Market", "url": "https://news.google.com/rss/search?q=(options+market+OR+options+trading+OR+put+call+ratio+OR+VIX)+when:2d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Futures Trading", "url": "https://news.google.com/rss/search?q=(futures+trading+OR+S%26P+500+futures+OR+Nasdaq+futures)+when:1d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "fintech": [
        {"name": "Fintech News", "url": "https://news.google.com/rss/search?q=(fintech+OR+payment+technology+OR+neobank+OR+digital+banking)+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Trading Tech", "url": "https://news.google.com/rss/search?q=(algorithmic+trading+OR+trading+platform+OR+quantitative+finance)+when:7d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Blockchain Finance", "url": "https://news.google.com/rss/search?q=(blockchain+finance+OR+tokenization+OR+digital+securities+OR+CBDC)+when:7d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "regulation": [
        {"name": "SEC", "url": "https://www.sec.gov/news/pressreleases.rss"},
        {"name": "Financial Regulation", "url": "https://news.google.com/rss/search?q=(SEC+OR+CFTC+OR+FINRA+OR+FCA)+regulation+OR+enforcement+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Banking Rules", "url": "https://news.google.com/rss/search?q=(Basel+OR+capital+requirements+OR+banking+regulation)+when:7d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Crypto Regulation", "url": "https://news.google.com/rss/search?q=(crypto+regulation+OR+digital+asset+regulation+OR+stablecoin+regulation)+when:7d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "institutional": [
        {"name": "Hedge Fund News", "url": "https://news.google.com/rss/search?q=(hedge+fund+OR+Bridgewater+OR+Citadel+OR+Renaissance)+when:7d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Private Equity", "url": "https://news.google.com/rss/search?q=(private+equity+OR+Blackstone+OR+KKR+OR+Apollo+OR+Carlyle)+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Sovereign Wealth", "url": "https://news.google.com/rss/search?q=(sovereign+wealth+fund+OR+pension+fund+OR+institutional+investor)+when:7d&hl=en-US&gl=US&ceid=US:en"},
    ],
    "analysis": [
        {"name": "Market Outlook", "url": "https://news.google.com/rss/search?q=(market+outlook+OR+stock+market+forecast+OR+bull+market+OR+bear+market)+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Risk & Volatility", "url": "https://news.google.com/rss/search?q=(VIX+OR+market+volatility+OR+risk+off+OR+market+correction)+when:3d&hl=en-US&gl=US&ceid=US:en"},
        {"name": "Bank Research", "url": "https://news.google.com/rss/search?q=(Goldman+Sachs+OR+JPMorgan+OR+Morgan+Stanley)+forecast+OR+outlook+when:3d&hl=en-US&gl=US&ceid=US:en"},
    ],
}
