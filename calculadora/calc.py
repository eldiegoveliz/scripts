import yfinance as yf
import pandas as pd
import numpy as np

def calculate_target_price(ticker_symbol):
    print(f"--- Analyzing {ticker_symbol} ---")
    
    # 1. Fetch Data
    stock = yf.Ticker(ticker_symbol)
    financials = stock.financials.T  # Transpose for easier access
    balance_sheet = stock.balance_sheet.T
    
    # Check if we have enough data
    if financials.empty or 'EBITDA' not in financials.columns:
        print("Error: Could not retrieve EBITDA data.")
        return

    # 2. Get EBITDA Data (Reverse to have chronological order: Oldest -> Newest)
    ebitda_series = financials['EBITDA'].iloc[::-1]
    
    # 3. Calculate EBITDA Growth (CAGR)
    # We use whatever history is available (usually 4 years for free yfinance)
    years_available = len(ebitda_series) - 1
    if years_available < 1:
        print("Not enough data to calculate growth.")
        return
        
    start_ebitda = ebitda_series.iloc[0]
    end_ebitda = ebitda_series.iloc[-1]
    
    # CAGR Formula
    ebitda_cagr = (end_ebitda / start_ebitda) ** (1 / years_available) - 1
    
    print(f"Data Points Available: {years_available + 1} years")
    print(f"Calculated EBITDA CAGR: {ebitda_cagr:.2%}")

    # 4. Calculate Historical EV/EBITDA Multiple
    # Note: Getting historical EV requires historical share prices and debt. 
    # For this script, we will calculate the CURRENT EV/EBITDA as a proxy, 
    # but I've added a variable to manually override if you have a specific 10-year avg.
    
    try:
        current_info = stock.info
        current_ev = current_info.get('enterpriseValue')
        current_ebitda_ttm = current_info.get('ebitda')
        
        if current_ev and current_ebitda_ttm:
            implied_multiple = current_ev / current_ebitda_ttm
        else:
            # Fallback calculation
            implied_multiple = 10.0 # Standard placeholder if data is missing
            
        print(f"Current EV/EBITDA Multiple: {implied_multiple:.2f}x")
        
    except Exception as e:
        print(f"Could not fetch live multiples: {e}")
        implied_multiple = 10.0

    # USER CONFIGURABLE: Override this if you know the specific 10-year average
    avg_ev_ebitda_multiple = implied_multiple 

    # 5. Forecast EBITDA (10 Years)
    future_years = 10
    future_ebitda = end_ebitda * ((1 + ebitda_cagr) ** future_years)
    
    print(f"Current EBITDA: ${end_ebitda:,.0f}")
    print(f"Forecasted EBITDA (Year {future_years}): ${future_ebitda:,.0f}")

    # 6. Calculate Forecasted Enterprise Value
    forecasted_ev = future_ebitda * avg_ev_ebitda_multiple

    # 7. Adjust for Net Debt to get Equity Value
    # Formula: Equity Value = EV + Cash - Debt
    
    try:
        # Get most recent Balance Sheet items
        recent_bs = balance_sheet.iloc[0] 
        cash_and_equivalents = recent_bs.get('Cash And Cash Equivalents', 0)
        
        # Try to find Total Debt (naming varies in yfinance)
        total_debt = recent_bs.get('Total Debt', 0)
        if total_debt == 0:
             total_debt = recent_bs.get('Long Term Debt', 0) + recent_bs.get('Current Debt', 0)

        shares_outstanding = stock.info.get('sharesOutstanding')
        
        equity_value = forecasted_ev + cash_and_equivalents - total_debt
        
        # 8. Calculate Share Price
        target_share_price = equity_value / shares_outstanding
        
        print("-" * 30)
        print(f"Forecasted EV: ${forecasted_ev:,.0f}")
        print(f"(-) Total Debt: ${total_debt:,.0f}")
        print(f"(+) Cash: ${cash_and_equivalents:,.0f}")
        print(f"(=) Future Equity Value: ${equity_value:,.0f}")
        print("-" * 30)
        print(f"PREDICTED STOCK PRICE (Year {future_years}): ${target_share_price:,.2f}")
        
        # Optional: Compare to current price
        current_price = stock.history(period='1d')['Close'].iloc[0]
        upside = (target_share_price - current_price) / current_price
        print(f"Current Price: ${current_price:,.2f}")
        print(f"Potential Upside: {upside:.2%}")

    except Exception as e:
        print(f"Error in calculation details: {e}")

# --- RUN THE SCRIPT ---
# Example: Apple (AAPL)
calculate_target_price("SRPT")
