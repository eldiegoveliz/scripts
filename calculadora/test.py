import yfinance as yf
import pandas as pd
import numpy as np

import yahoofinancials as yfs

from yahoofinancials import IncomeStatement

#ticker = yf.Ticker ("LMT")
#info = ticker.info
#ebitda = info["ebitda"]
#print(f"EBITDA: {ebitda}")
#print(ticker.quarterly_financials)

tickerf = "LMT"
financ = yfs.YahooFinancials(tickerf)
inc_stmnt = financ.get_financial_stmts("annual", "income")
#print(f"INC: {inc_stmnt}")

inc = IncomeStatement(tickerf)
dfs = inc.to_dfs()
rev_df = dfs["Rev"]
print(Rev)
