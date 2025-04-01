import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

# ✅ Investment Categories & Market Proxies
CATEGORIES = {
    "Equity": ["^NSEI"],  # Nifty 50
    "Mutual Funds": ["ICICIPRAMC.NS"],  # Mutual Fund Example
    "Bonds": ["^IRX"],  # Treasury Bonds
    "Gold": ["GC=F"],  # Gold Futures
    "Real Estate": ["VNQ"]  # REITs (Replace with Indian REITs)
}

# ✅ Fetch Historical Data
def get_historical_data(ticker, period="5y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    
    if data.empty:
        print(f"❌ No data for {ticker}")
        return None
    
    return data[["Close"]].reset_index().rename(columns={"Close": "price"})

# ✅ Compute CAGR (Compounded Annual Growth Rate)
def calculate_cagr(start_price, end_price, years):
    if start_price is None or end_price is None or years <= 0 or start_price == 0:
        return 0  # Prevent division errors
    return (end_price / start_price) ** (1 / years) - 1

# ✅ Compute Standard Deviation (Risk Measure)
def calculate_risk(data):
    if data is None or data.empty:
        return 0  # Default risk if no data available
    return np.std(data["price"].pct_change().dropna())  # Daily return standard deviation

# ✅ Compute Correlation Matrix for Asset Returns
def calculate_correlation_matrix():
    price_data = []
    
    for tickers in CATEGORIES.values():
        data = get_historical_data(tickers[0], period="5y")
        if data is not None:
            price_data.append(data["price"].pct_change().dropna())

    if len(price_data) == len(CATEGORIES):  # Ensure all assets have data
        correlation_matrix = np.corrcoef(price_data)
    else:
        correlation_matrix = np.eye(len(CATEGORIES))  # Use identity matrix if missing data

    return correlation_matrix

# ✅ Fetch Past CAGR & Risk for Each Asset
def get_past_data():
    cagr_values = {}
    risk_values = {}

    for category, tickers in CATEGORIES.items():
        ticker = tickers[0]
        data = get_historical_data(ticker, period="5y")

        if data is None or data.empty:
            cagr_values[category] = 0  # Default to zero
            risk_values[category] = 0
            continue

        start_price = data["price"].iloc[0]
        end_price = data["price"].iloc[-1]
        years = 5  # Using 5 years of data

        cagr_values[category] = calculate_cagr(start_price, end_price, years)
        risk_values[category] = calculate_risk(data)

    correlation_matrix = calculate_correlation_matrix()

    print(f"📊 Past CAGR Data: {cagr_values}")  # Debugging Output
    print(f"⚠️ Risk Data (Volatility): {risk_values}")  # Debugging Output
    return cagr_values, risk_values, correlation_matrix

# ✅ Optimization Function using Sharpe Ratio (Return/Risk)
def optimize_allocation(investment_amount):
    cagr_data, risk_data, correlation_matrix = get_past_data()

    # ✅ Ensure flat NumPy arrays
    returns = np.array([cagr_data[key] for key in CATEGORIES])
    risks = np.array([risk_data[key] for key in CATEGORIES])

    # ✅ Validate Correlation Matrix
    if not isinstance(correlation_matrix, np.ndarray) or correlation_matrix.shape != (len(CATEGORIES), len(CATEGORIES)):
        print("⚠️ Invalid correlation matrix, using identity matrix.")
        correlation_matrix = np.eye(len(CATEGORIES))  # Default to identity matrix

    num_assets = len(CATEGORIES)

    # ✅ Objective function: Maximize Sharpe Ratio with risk penalty
    def neg_sharpe(weights):
        expected_return = np.dot(weights, returns)
        portfolio_risk = np.sqrt(np.dot(weights.T, np.dot(correlation_matrix, weights)))
        risk_penalty = 100 * abs(np.sum(weights) - 1)  # Penalty for weights not summing to 1
        return -(expected_return - 0.5 * portfolio_risk) + risk_penalty

    # ✅ Constraints: Sum of weights = 1 (strict equality)
    constraints = [
        {'type': 'eq', 'fun': lambda w: np.sum(w) - 1}
    ]

    # ✅ Ensure bounds are properly structured with tighter constraints
    bounds = [
        (0.15, 0.40),  # Equity: 15%-40%
        (0.10, 0.30),  # Mutual Funds: 10%-30%
        (0.10, 0.30),  # Bonds: 10%-30%
        (0.10, 0.25),  # Gold: 10%-25%
        (0.10, 0.25),  # Real Estate: 10%-25%
    ]

    # Initial Guess: Equal allocation
    initial_guess = np.array([1 / num_assets] * num_assets)

    # Optimize with increased iterations and tolerance
    result = minimize(neg_sharpe, initial_guess, 
                     bounds=bounds, 
                     constraints=constraints,
                     method='SLSQP',
                     options={'maxiter': 1000, 'ftol': 1e-8})

    if result.success:
        # Normalize weights to ensure they sum exactly to 1
        optimized_weights = result.x / np.sum(result.x)
        
        # Calculate raw allocations
        raw_allocations = {category: weight * investment_amount 
                         for category, weight in zip(CATEGORIES.keys(), optimized_weights)}
        
        # Round allocations while preserving total
        total = sum(raw_allocations.values())
        rounded_allocations = {}
        running_total = 0
        
        # Round all but the last category
        categories = list(CATEGORIES.keys())
        for category in categories[:-1]:
            amount = round(raw_allocations[category], 2)
            rounded_allocations[category] = amount
            running_total += amount
        
        # Adjust last category to ensure exact total
        rounded_allocations[categories[-1]] = round(investment_amount - running_total, 2)
        
        allocation = rounded_allocations
    else:
        print("❌ Optimization failed. Using equal allocation.")
        amount_per_asset = round(investment_amount / num_assets, 2)
        allocation = {cat: amount_per_asset for cat in list(CATEGORIES.keys())[:-1]}
        # Adjust last category for rounding errors
        allocation[list(CATEGORIES.keys())[-1]] = round(investment_amount - sum(allocation.values()), 2)

    # Verify total allocation matches investment amount
    total_allocated = sum(allocation.values())
    print(f"✅ Total Allocated: {total_allocated} (Target: {investment_amount})")
    print(f"✅ Allocation Weights: {[round(v/investment_amount, 4) for v in allocation.values()]}")
    
    return allocation

