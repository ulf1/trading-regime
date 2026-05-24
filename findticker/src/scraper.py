import sys
import logging
import requests
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

REGIONS = ["us", "ca", "gb", "de", "fr", "it", "es", "nl", "be", "at", "ch", "pt", "ie", "lu", "mc", "se", "no", "dk", "fi", "is", "pl", "cz", "sk", "hu", "ro", "bg", "hr", "si", "ee", "lv", "lt", "gr", "cy", "mt", "rs", "ba", "me", "mk", "al", "tr", "ua"]

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

def fetch_historical_data(ticker: str) -> pd.DataFrame:
    logger.info(f"Fetching historical data for {ticker}...")
    try:
        data = yf.download([ticker], period="max", interval="1d", auto_adjust=False, threads=False, progress=False)
        if data.empty or 'Adj Close' not in data.columns:
            return pd.DataFrame()
            
        ticker_df = data[['Adj Close']].dropna().copy()
        ticker_df = ticker_df.reset_index()
        ticker_df['ticker'] = ticker
        ticker_df['Date'] = ticker_df['Date'].dt.strftime('%Y-%m-%d')
        ticker_df = ticker_df.rename(columns={'Date': 'date', 'Adj Close': 'adj_close'})
        
        # Unpack MultiIndex columns if necessary
        if isinstance(ticker_df.columns, pd.MultiIndex):
            ticker_df.columns = [col[0] for col in ticker_df.columns]
            
        return ticker_df
    except Exception as e:
        logger.error(f"Error fetching history for {ticker}: {e}")
        return pd.DataFrame()
