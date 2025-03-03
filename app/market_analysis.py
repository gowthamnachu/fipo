import numpy as np
import yfinance as yf

def get_past_returns():
    """Fetch past CAGR returns for different investment categories from Yahoo Finance."""
    symbols = {
        "Equity": "^NSEI",  # Nifty 50 (India's stock index)
        "Mutual Funds": "ICICIPRAMC.NS",  # ICICI Mutual Fund (Example)
        "Bonds": "BND",  # Vanguard Bond ETF
        "Gold": "GC=F",  # Gold Futures
        "Real Estate": "VNQ"  # Real Estate ETF
    }

    past_returns = []
    
    for category, symbol in symbols.items():
        try:
            data = yf.download(symbol, period="5y", interval="1mo")['Adj Close']
            if len(data) > 1:
                cagr = (data[-1] / data[0]) ** (1 / 5) - 1  # CAGR formula
                past_returns.append(cagr)
            else:
                raise Exception("Not enough data points")
        except Exception as e:
            print(f"⚠ Error fetching {category} ({symbol}): {e}")
            past_returns.append(0.05)  # Default to 5% if data fails

    print("📊 Past CAGR Data:", past_returns)  # Debugging
    return np.array(past_returns)
