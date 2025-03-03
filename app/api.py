import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_live_market_data(tickers):
    """
    Fetch real-time market prices for given tickers.
    """
    stock_data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                stock_data[ticker] = {
                    "price": hist["Close"].iloc[-1]
                }
            else:
                stock_data[ticker] = {"price": None}  # Handle missing data
        except Exception as e:
            print(f"⚠ Error fetching live price for {ticker}: {e}")
            stock_data[ticker] = {"price": None}
    
    return stock_data

def get_historical_market_data(ticker, period="5y"):
    """
    Fetch historical price data and calculate CAGR (Compound Annual Growth Rate).
    """
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period)
        
        if data.empty:
            raise Exception(f"No data for {ticker}")

        start_price = data["Close"].iloc[0]
        end_price = data["Close"].iloc[-1]

        if start_price > 0:
            years = int(period[0])  # Extracts the number of years from "5y"
            cagr = (end_price / start_price) ** (1 / years) - 1
        else:
            cagr = 0.05  # Default 5% if calculation fails

        return {"historical_data": data[["Close"]].reset_index(), "cagr": cagr}
    
    except Exception as e:
        print(f"⚠ Error fetching historical data for {ticker}: {e}")
        return {"historical_data": None, "cagr": 0.05}  # Default 5% CAGR

