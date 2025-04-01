import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import asyncio
import requests
import time
from functools import lru_cache

# Cache for storing market data with 10-second expiry
MARKET_DATA_CACHE = {}
CACHE_EXPIRY = 10  # seconds

# Rate limiting configuration
REQUEST_LIMIT = 2  # Reduced from 5 to 2 requests per second
REQUEST_WINDOW = 2  # Increased from 1 to 2 seconds
request_timestamps = []
REQUEST_QUEUE = asyncio.Queue()

async def check_rate_limit():
    """Implement rate limiting for API requests with queuing"""
    current_time = time.time()
    request_timestamps[:] = [t for t in request_timestamps if current_time - t < REQUEST_WINDOW]
    
    if len(request_timestamps) >= REQUEST_LIMIT:
        wait_time = REQUEST_WINDOW - (current_time - request_timestamps[0])
        if wait_time > 0:
            await asyncio.sleep(wait_time)
            # Clear expired timestamps after waiting
            request_timestamps[:] = [t for t in request_timestamps if current_time - t < REQUEST_WINDOW]
    
    request_timestamps.append(current_time)

async def get_live_market_data(tickers):
    """Fetch real-time market prices with enhanced error handling and rate limiting"""
    stock_data = {}
    current_time = datetime.now()
    
    for ticker in tickers:
        try:
            # Check rate limit with queuing
            await check_rate_limit()
            
            # Check cache first
            cached_data = MARKET_DATA_CACHE.get(ticker)
            if cached_data and (time.time() - cached_data['timestamp'] < CACHE_EXPIRY):
                stock_data[ticker] = cached_data['data']
                continue

            # Use yfinance as primary source
            stock = yf.Ticker(ticker)
            hist = stock.history(period='1d', interval='1m', prepost=True)
            
            # Add delay between consecutive requests
            await asyncio.sleep(0.5)
            
            if not hist.empty:
                latest_data = hist.iloc[-1]
                open_price = hist['Open'].iloc[0] if len(hist) > 0 else 0
                current_price = latest_data['Close']
                price_change = ((current_price - open_price) / open_price * 100) if open_price > 0 else 0
                
                # Validate data
                if not isinstance(current_price, (int, float)) or current_price < 0:
                    raise ValueError(f"Invalid price data for {ticker}")
                
                # Format timestamp
                timestamp = latest_data.name
                formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S') if isinstance(timestamp, (pd.Timestamp, datetime)) else current_time.strftime('%Y-%m-%d %H:%M:%S')
                
                market_data = {
                    "price": round(float(current_price), 2),
                    "change": round(float(price_change), 2),
                    "volume": int(latest_data['Volume']),
                    "high": round(float(latest_data['High']), 2),
                    "low": round(float(latest_data['Low']), 2),
                    "timestamp": formatted_time,
                    "status": "success"
                }
                
                # Update cache with validation
                if all(v is not None for v in market_data.values()):
                    MARKET_DATA_CACHE[ticker] = {
                        'data': market_data,
                        'timestamp': time.time()
                    }
                    stock_data[ticker] = market_data
                else:
                    raise ValueError(f"Incomplete market data for {ticker}")
            else:
                raise ValueError(f"No data available for {ticker}")
                
        except Exception as e:
            print(f"⚠ Error fetching data for {ticker}: {str(e)}")
            stock_data[ticker] = {
                "price": 0.0,
                "change": 0.0,
                "volume": 0,
                "high": 0.0,
                "low": 0.0,
                "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S'),
                "status": "error",
                "error": str(e)
            }
    
    return stock_data

def get_historical_market_data(ticker, period="1d"):
    """
    Fetch historical price data with proper error handling.
    """
    try:
        stock = yf.Ticker(ticker)
        end_date = datetime.now()
        
        if period == "1d":
            # Get intraday data with 1-minute intervals for today
            start_date = end_date.strftime('%Y-%m-%d')
            data = stock.history(start=start_date, interval='1m')
        else:
            # For longer periods, use daily data
            data = stock.history(period=period)
        
        if data.empty:
            raise Exception(f"No data available for {ticker}")
        
        # Calculate price changes
        start_price = data['Close'].iloc[0]
        end_price = data['Close'].iloc[-1]
        price_change = ((end_price - start_price) / start_price) * 100
        
        return {
            "historical_data": data[['Open', 'High', 'Low', 'Close', 'Volume']].reset_index(),
            "price_change": price_change,
            "start_price": start_price,
            "end_price": end_price,
            "volume": data['Volume'].sum(),
            "period_high": data['High'].max(),
            "period_low": data['Low'].min()
        }
    
    except Exception as e:
        print(f"⚠ Error fetching historical data for {ticker}: {e}")
        return None

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

