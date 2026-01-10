import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
from datetime import datetime, timedelta
import os

ipsa = "^IPSA"
spy = "^GSPC"

tickers = ["^IPSA", "^GSPC"]

data = yf.download(tickers, period="5d", progress=False)

for ticker in tickers:
    opening_price = data["Open"][ticker].iloc[0] if not data.empty else "N/A"
    print(f"{ticker}: {opening_price}")

end_date = datetime.now()
start_date = end_date - timedelta(hours=9, minutes=30)
dataipsa = yf.download(ipsa, start=start_date, end=end_date, interval="5m")
dataspy = yf.download(spy, start=start_date, end=end_date, interval="5m")

#SEPARAR FIGS PARA TRABAJAR CADA SUBPLOT APARTE

plt.style.use("dark_background")
fig, (ax1, ax2) = plt.subplots(2, figsize=(4, 2))
#fig, ax2 = plt.subplots(figsize=(4, 2))

ax1.plot(dataipsa.index, dataipsa["Close"], color="white", linewidth=1)
ax2.plot(dataspy.index, dataspy["Close"], color="white", linewidth=1)

pipsa = yf.Ticker(ipsa)
pspy = yf.Ticker(spy)

op_ipsa = opening_price = data["Open"][ipsa].iloc[0]
cp_ipsa = pipsa.info["regularMarketPrice"]
op_spy = opening_price = data["Open"][spy].iloc[0]
cp_spy = pspy.info["regularMarketPrice"]

deltaipsa = ((cp_ipsa/op_ipsa)-1)*100
deltaspy = ((cp_spy/op_spy)-1)*100

if deltaipsa < 0:
    ax1.text(0.5, 0.95, f"IPSA", transform=ax1.transAxes, color="white", 
            fontsize=11, ha="center", va="top")
    ax1.text(0.02, -0.1, f"{op_ipsa:.2f}", transform=ax1.transAxes, 
            color="white", fontsize=9, ha="left", va ="top")
    ax1.text(0.5, -0.1, f"{deltaipsa:.2f}%", transform=ax1.transAxes, 
            color="red", fontsize=10, ha="center", va ="top")
    ax1.text(0.98, -0.1, f"{cp_ipsa:.2f}", transform=ax1.transAxes, color="white",
            fontsize=9, ha="right", va ="top")
else:

    ax1.text(0.02, -0.1, f"{op_ipsa:.2f}", transform=ax1.transAxes, color="white",
        fontsize=8, ha="left", va ="top")
    ax1.text(0.5, -0.1, f"IPSA: {deltaipsa:.2f}%", transform=ax1.transAxes, 
        color="green", fontsize=12, ha="center", va ="top")
    ax1.text(0.98, -0.1, f"{cp_ipsa:.2f}", transform=ax1.transAxes, color="white",
        fontsize=8, ha="right", va ="top")

ax1.set_axis_off()
plt.tight_layout(pad=2)

output_path = os.path.expanduser("~/scripts/testipsa.png")
plt.savefig(output_path, bbox_inches="tight", pad_inches=0, transparent=True)
plt.close()

#if deltaspy < 0:
#    ax2.text(0.5, 0.95, f"SPY", transform=ax2.transAxes, color="white", 
#            fontsize=11, ha="center", va="top")
#    ax2.text(0.02, -0.1, f"{op_spy:.2f}", transform=ax2.transAxes, 
#            color="white", fontsize=9, ha="left", va ="top")
#    ax2.text(0.5, -0.1, f"{deltaspy:.2f}%", transform=ax2.transAxes, 
#            color="red", fontsize=10, ha="center", va ="top")
#    ax2.text(0.98, -0.1, f"{cp_spy:.2f}", transform=ax2.transAxes, color="white",
#            fontsize=9, ha="right", va ="top")
#else:
#    ax2.text(0.5, 0.95, f"SPY", transform=ax2.transAxes, color="white", 
#            fontsize=11, ha="center", va="top")
#    ax2.text(0.02, -0.1, f"{op_spy:.2f}", transform=ax2.transAxes, color="white",
#        fontsize=8, ha="left", va ="top")
#    ax2.text(0.5, -0.1, f"{deltaspy:.2f}%", transform=ax2.transAxes, 
#        color="green", fontsize=12, ha="center", va ="top")
#    ax2.text(0.98, -0.1, f"{cp_spy:.2f}", transform=ax2.transAxes, color="white",
#        fontsize=8, ha="right", va ="top")
#
#ax2.set_axis_off()
#plt.tight_layout(pad=2)
#
#output_path = os.path.expanduser("~/scripts/testspy.png")
#plt.savefig(output_path, bbox_inches="tight", pad_inches=0, transparent=True)
#plt.close()


