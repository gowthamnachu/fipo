import asyncio
import websockets
import json
from datetime import datetime, timedelta
import sys
import os
import django

# Add the project root directory to Python path and configure Django settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fipo.settings')
django.setup()

from app.api import get_live_market_data, get_historical_market_data

async def generate_market_data():
    try:
        # Initialize default values and check market status
        current_time = datetime.now()
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Check if it's a weekend
        is_weekend = current_time.weekday() >= 5
        
        # Check market hours (9:15 AM to 3:30 PM IST)
        market_start = current_time.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = current_time.replace(hour=15, minute=30, second=0, microsecond=0)
        is_market_hours = market_start <= current_time <= market_end
        
        # Determine market status message
        if is_weekend:
            market_status = "Market is closed for the weekend"
        elif not is_market_hours:
            if current_time < market_start:
                market_status = "Market has not opened yet"
            else:
                market_status = "Market has closed for the day"
        else:
            market_status = "Market is open"
        default_market_data = {
            'price': 0.0,
            'change': 0.0,
            'volume': 0,
            'high': 0.0,
            'low': 0.0,
            'timestamp': current_time
        }

        # Fetch live market data for indices with retries
        retries = 3
        for _ in range(retries):
            try:
                nifty_data = await get_live_market_data(['^NSEI'])
                sensex_data = await get_live_market_data(['^BSESN'])
                if nifty_data and sensex_data:
                    break
            except Exception as e:
                print(f"Retrying market data fetch: {e}")
                await asyncio.sleep(1)

        # Ensure we have valid data objects
        nifty_data = nifty_data or {'^NSEI': default_market_data.copy()}
        sensex_data = sensex_data or {'^BSESN': default_market_data.copy()}

        # Fetch live data for top stocks with validation
        market_tickers = ['TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'RELIANCE.NS', 'ICICIBANK.NS']
        market_data = await get_live_market_data(market_tickers) or {}

        # Format indices data with proper validation
        indices = [
            {
                "name": "NIFTY 50",
                "value": float(nifty_data.get('^NSEI', {}).get('price', 0)),
                "change": float(nifty_data.get('^NSEI', {}).get('change', 0)),
                "volume": int(nifty_data.get('^NSEI', {}).get('volume', 0)),
                "high": float(nifty_data.get('^NSEI', {}).get('high', 0)),
                "low": float(nifty_data.get('^NSEI', {}).get('low', 0)),
                "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                "name": "SENSEX",
                "value": float(sensex_data.get('^BSESN', {}).get('price', 0)),
                "change": float(sensex_data.get('^BSESN', {}).get('change', 0)),
                "volume": int(sensex_data.get('^BSESN', {}).get('volume', 0)),
                "high": float(sensex_data.get('^BSESN', {}).get('high', 0)),
                "low": float(sensex_data.get('^BSESN', {}).get('low', 0)),
                "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        # Format market stocks data with advanced metrics
        market_stocks = []
        for ticker in market_tickers:
            stock_data = market_data.get(ticker, {})
            if stock_data:
                stock_name = ticker.replace('.NS', '')
                price = stock_data.get('price', 0)
                volume = stock_data.get('volume', 0)
                high = stock_data.get('high', 0)
                low = stock_data.get('low', 0)
                change = stock_data.get('change', 0)
                
                # Calculate additional technical indicators
                vwap = (high + low + price) / 3 * volume if volume > 0 else price
                price_range = high - low if high and low else 0
                volatility = (price_range / price * 100) if price > 0 else 0
                momentum = ((price - low) / (high - low) * 100) if high != low else 50
                
                market_stocks.append({
                    "name": stock_name,
                    "price": round(price, 2),
                    "change": round(change, 2),
                    "volume": volume,
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "vwap": round(vwap, 2),
                    "volatility": round(volatility, 2),
                    "momentum": round(momentum, 2),
                    "price_range": round(price_range, 2),
                    "volume_change": round(stock_data.get('volume_change', 0), 2),
                    "market_cap": stock_data.get('market_cap', 0),
                    "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort stocks by real-time percentage change and filter out invalid data
        valid_stocks = [stock for stock in market_stocks if stock['price'] > 0]
        # Sort by absolute percentage change to include both gainers and losers
        valid_stocks.sort(key=lambda x: (abs(x['change']), x['volume']), reverse=True)
        # Filter top gainers (positive change)
        gainers = [stock for stock in valid_stocks if stock['change'] > 0]
        market_stocks = gainers or valid_stocks  # Fallback to all stocks if no gainers found
        
        # Get trend data with more frequent updates
        nifty_trend = get_historical_market_data('^NSEI', period='1d')
        if nifty_trend and 'historical_data' in nifty_trend:
            trend_data = nifty_trend['historical_data']
            labels = [timestamp.strftime('%H:%M:%S') for timestamp in trend_data['Date']]
            values = trend_data['Close'].tolist()
            if len(labels) > 100:
                labels = labels[-100:]
                values = values[-100:]
        else:
            labels = []
            values = []
        
        return {
            "indices": indices,
            "gainers": market_stocks[:5],
            "trendData": {
                "labels": labels,
                "values": values,
                "updated_at": formatted_time
            },
            "marketStatus": {
                "status": market_status,
                "isOpen": not is_weekend and is_market_hours
            }
        }
    except Exception as e:
        print(f"Error generating market data: {e}")
        return {
            "indices": [
                {
                    "name": "NIFTY 50",
                    "value": 0,
                    "change": 0,
                    "volume": 0,
                    "high": 0,
                    "low": 0,
                    "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S')
                },
                {
                    "name": "SENSEX",
                    "value": 0,
                    "change": 0,
                    "volume": 0,
                    "high": 0,
                    "low": 0,
                    "timestamp": current_time.strftime('%Y-%m-%d %H:%M:%S')
                }
            ],
            "gainers": [],
            "trendData": {
                "labels": [],
                "values": [],
                "updated_at": current_time
            }
        }

async def send_market_updates(websocket):
    connection_id = id(websocket)
    print(f"New connection established: {connection_id}")
    retry_count = 0
    max_retries = 3
    backoff_delay = 1

    try:
        while True:
            try:
                # Generate market data with retry mechanism
                data = None
                for attempt in range(max_retries):
                    try:
                        data = await generate_market_data()
                        if data:
                            break
                        print(f"Attempt {attempt + 1}: No market data available")
                    except Exception as e:
                        print(f"Attempt {attempt + 1} failed: {e}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(backoff_delay * (2 ** attempt))
                
                if not data:
                    print("Failed to generate market data after retries")
                    await asyncio.sleep(5)
                    continue

                # Validate data structure and timestamps
                current_time = datetime.now()
                data_age = 0
                
                # Validate indices data
                if not isinstance(data.get('indices'), list):
                    print("Invalid indices data structure")
                    continue

                for index in data.get('indices', []):
                    if not all(key in index for key in ['name', 'value', 'timestamp']):
                        print(f"Missing required fields in index data: {index}")
                        continue

                    try:
                        # Ensure timestamp is a string before parsing
                        timestamp_str = index['timestamp'] if isinstance(index['timestamp'], str) else index['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        data_age = (current_time - timestamp).seconds
                        if data_age > 60:
                            print(f"Data is {data_age} seconds old, refreshing...")
                            data = await generate_market_data()
                            break
                    except ValueError as e:
                        print(f"Invalid timestamp format: {e}")
                        continue

                # Validate gainers data
                if not isinstance(data.get('gainers'), list):
                    print("Invalid gainers data structure")
                    continue

                # Send data with health check
                try:
                    await websocket.send(json.dumps(data))
                    retry_count = 0  # Reset retry counter on successful send
                    await asyncio.sleep(2)  # Delay between updates
                except websockets.exceptions.ConnectionClosed:
                    print(f"Connection {connection_id} closed")
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count > max_retries:
                        print(f"Connection {connection_id} exceeded max retries")
                        break
                    print(f"Error sending data (attempt {retry_count}): {e}")
                    await asyncio.sleep(backoff_delay * (2 ** retry_count))

            except websockets.exceptions.ConnectionClosed:
                print(f"Connection {connection_id} closed by client")
                break
            except json.JSONDecodeError as e:
                print(f"JSON encoding error: {e}")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error in market updates: {e}")
                await asyncio.sleep(5)
    finally:
        print(f"Connection {connection_id} terminated")
        try:
            await websocket.close()
        except:
            pass
        print("Market updates stopped")

async def handle_connection(websocket):
    print(f"Client connected from {websocket.remote_address}")
    try:
        await send_market_updates(websocket)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print(f"Client disconnected from {websocket.remote_address}")

import os
from django.conf import settings

async def start_server():
    try:
        # Start WebSocket server
        server = await websockets.serve(send_market_updates, 'localhost', 8765)
        print("WebSocket server started on ws://localhost:8765")
        await asyncio.Future()  # Keep the server running
    except Exception as e:
        print(f"Error starting WebSocket server: {e}")

if __name__ == "__main__":
    asyncio.run(start_server())