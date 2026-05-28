import sys
import logging
import requests
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

REGIONS = [
    # North America
    "us",   # United States
    "ca",   # Canada

    # Western Europe
    "gb",   # United Kingdom
    "de",   # Germany
    "fr",   # France (Euronext)
    "it",   # Italy (Euronext)
    "es",   # Spain
    "nl",   # Netherlands (Euronext)
    "be",   # Belgium (Euronext)
    "at",   # Austria 
    "ch",   # Switzerland
    "pt",   # Portugal (Euronext)
    "ie",   # Ireland (Euronext)
    "lu",   # Luxembourg
    "mc",   # Monaco

    # Northern Europe
    "se",   # Sweden (Nasdaq Nordic)
    "no",   # Norway (Euronext)
    "dk",   # Denmark (Nasdaq Nordic)
    "fi",   # Finland (Nasdaq Nordic)
    "is",   # Iceland (Nasdaq Nordic)

    # Eastern Europe
    "pl",   # Poland
    "cz",   # Czech Republic
    "sk",   # Slovakia
    "hu",   # Hungary
    "ro",   # Romania
    "bg",   # Bulgaria
    "hr",   # Croatia
    "si",   # Slovenia
    "ee",   # Estonia (Nasdaq Baltic)
    "lv",   # Latvia (Nasdaq Baltic)
    "lt",   # Lithuania (Nasdaq Baltic)

    # Southern / Southeastern Europe
    "gr",   # Greece (Euronext)
    "cy",   # Cyprus
    "mt",   # Malta
    "rs",   # Serbia
    "ba",   # Bosnia and Herzegovina
    "me",   # Montenegro
    "mk",   # North Macedonia
    "al",   # Albania
    "tr",   # Turkey

    # Other European
    "ua",   # Ukraine
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def get_session_and_crumb() -> tuple[requests.Session, str]:
    session = requests.Session()
    session.headers.update(HEADERS)
    try:
        session.get("https://finance.yahoo.com", timeout=15, allow_redirects=True)
        crumb_url = "https://query1.finance.yahoo.com/v1/test/getcrumb"
        crumb_resp = session.get(crumb_url, timeout=10)
        if crumb_resp.status_code != 200 or not crumb_resp.text.strip():
            crumb_url2 = "https://query2.finance.yahoo.com/v1/test/getcrumb"
            crumb_resp = session.get(crumb_url2, timeout=10)
            crumb_resp.raise_for_status()
        crumb = crumb_resp.text.strip()
        if not crumb:
            raise RuntimeError("Failed to retrieve Yahoo Finance crumb token.")
        return session, crumb
    except Exception as e:
        logger.error(f"Failed to get crumb: {e}")
        return session, ""

def build_screener_payload(regions: list[str], size: int = 20) -> dict:
    region_operands = [{"operator": "EQ", "operands": ["region", r]} for r in regions]
    return {
        "offset": 0,
        "size": size,
        "sortField": "dayvolume",
        "sortType": "DESC",
        "quoteType": "EQUITY",
        "query": {
            "operator": "AND",
            "operands": [{"operator": "or", "operands": region_operands}],
        },
        "userId": "",
        "userIdType": "guid",
    }

def fetch_most_active(session: requests.Session, crumb: str, regions: list[str], top_n: int = 20) -> list[str]:
    if not crumb:
        return []
    url = "https://query1.finance.yahoo.com/v1/finance/screener"
    params = {"crumb": crumb, "lang": "en-US", "region": "US", "formatted": "false", "corsDomain": "finance.yahoo.com"}
    payload = build_screener_payload(regions, size=top_n)
    
    try:
        resp = session.post(url, params=params, json=payload, timeout=15)
        if resp.status_code != 200:
            url2 = "https://query2.finance.yahoo.com/v1/finance/screener"
            resp = session.post(url2, params=params, json=payload, timeout=15)
            resp.raise_for_status()
        data = resp.json()
        quotes = data["finance"]["result"][0]["quotes"]
        return [q.get("symbol") for q in quotes if q.get("symbol")]
    except Exception as e:
        logger.error(f"Error fetching most active: {e}")
        return []

def scrape_new_tickers(top_n: int = 20) -> list[str]:
    session, crumb = get_session_and_crumb()
    return fetch_most_active(session, crumb, REGIONS, top_n)

def is_valid_equity_ticker(ticker: str) -> bool:
    """
    Performs validation checks to filter out professional debt instruments,
    structured bonds, warrants, preferred shares, and derivatives,
    ensuring that only standard stocks/equity instruments are kept.
    """
    # 1. Skip Oslo professional bonds listed on Oslo Børs / Nordic ABM
    if "-PRO" in ticker:
        return False
        
    # 2. Skip common derivative/warrant/preferred/unit suffixes
    # Warrants (-W, .W, .WS), Units (-U, .U), Preferred (-P), Futures (=F)
    for suffix in ["-W", ".W", ".WS", "-U", ".U", "-P", "=F"]:
        if suffix in ticker:
            return False
            
    # 3. Skip bond-like listings which typically contain digits and a hyphen in the symbol part
    # Example: 'SB1NO47-PRO.OL' or other structured debt products
    symbol_part = ticker.split(".")[0] if "." in ticker else ticker
    if "-" in symbol_part and any(char.isdigit() for char in symbol_part):
        return False
        
    return True


def get_market_cap_usd(symbol: str) -> float:
    """
    Return a company's market cap in USD using yfinance.
    
    Example:
        get_market_cap_usd("AAPL")
        get_market_cap_usd("SAP.DE")
    """

    ticker = yf.Ticker(symbol)
    info = ticker.info

    market_cap = info.get("marketCap")
    currency = info.get("currency")

    if market_cap is None:
        raise ValueError(f"No market cap available for {symbol}")

    # Already USD
    if currency == "USD":
        return float(market_cap)

    # Convert to USD using FX rate
    fx_pair = f"{currency}USD=X"

    try:
        fx_rate = yf.Ticker(fx_pair).history(period="1d")["Close"].iloc[-1]
    except Exception:
        raise ValueError(f"Could not fetch FX rate for {currency}->USD")

    return float(market_cap * fx_rate)


def fetch_historical_data(ticker: str) -> pd.DataFrame:
    """
    Fetches historical adjusted close prices for a ticker using yfinance.
    Normalizes MultiIndex outputs and formats the dataset for sqlite injection.
    """
    if not is_valid_equity_ticker(ticker):
        logger.info(f"Skipping non-equity ticker: {ticker}")
        return pd.DataFrame()

    logger.info(f"Fetching market cap for {ticker}...")
    market_cap = get_market_cap_usd(ticker)
    if market_cap < 2e9:
        logger.info(f"Skipping {ticker} with market cap {market_cap} (less than 250M USD)")
        return pd.DataFrame()

    logger.info(f"Fetching historical data for {ticker}...")
    try:
        # Pass ticker as string instead of a list to yf.download to obtain a standard single-index DataFrame
        data = yf.download(ticker, period="9y", interval="1d", auto_adjust=False, threads=False, progress=False)
        if data.empty:
            return pd.DataFrame()
            
        # Flatten MultiIndex columns immediately if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        if 'Adj Close' not in data.columns:
            logger.warning(f"No 'Adj Close' column found for {ticker}. Columns: {list(data.columns)}")
            return pd.DataFrame()
            
        # Extract Adj Close and drop missing observations
        ticker_df = data[['Adj Close']].dropna().copy()
        
        # Directly format dates from Datetime index to avoid key lookup errors (e.g. index named 'index')
        ticker_df['date'] = pd.to_datetime(ticker_df.index).strftime('%Y-%m-%d')
        ticker_df['ticker'] = ticker
        
        # Rename price column and order standard output schema
        ticker_df = ticker_df.rename(columns={'Adj Close': 'adj_close'})
        return ticker_df[['date', 'ticker', 'adj_close']]
    except Exception as e:
        logger.error(f"Error fetching history for {ticker}: {e}")
        return pd.DataFrame()
