import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os 

portfolio_positions = {
    "SRPT": 7,
    "GOVZ": 20,
    "SLNO": 3,
    "ABVX": 3.1798,



    "QCLS": 2,
}

cash = 0.65

def get_portfolio_performance(positions, cash_holdings):
    tickers = list(positions.keys())
    print("--- Iniciando proceso ---")
    print(f"Obteniendo datos de: {', '.join(tickers)}")
    try:
        df = yf.download(tickers, period="1d", interval="1m", prepost=True, progress=False)['Close']
    except Exception as e:
        print(f"Error descargando datos: {e}")
        return None, None, None

    if len(tickers) == 1:
        df = df.to_frame(name=tickers[0])        
    df = df.ffill().bfill()
    
    total_prev_close = cash_holdings
    
    print("Calculando cierre anterior...")
    for ticker in tickers:
        try:
            ticker_obj = yf.Ticker(ticker)
            prev = ticker_obj.info.get('regularMarketPreviousClose', df[ticker].iloc[0])
            total_prev_close += prev * positions[ticker]
        except Exception as e:
            print(f"Aviso: No se pudo obtener previousClose para {ticker}, usando primer dato del día. Error: {e}")
            total_prev_close += df[ticker].iloc[0] * positions[ticker]

    portfolio_value = pd.Series(cash_holdings, index=df.index)
    for ticker, qty in positions.items():
        portfolio_value += df[ticker] * qty
        

    pct_change = ((portfolio_value - total_prev_close) / total_prev_close) * 100    
    return pct_change, portfolio_value.iloc[-1], total_prev_close

def plot_and_save_chart(series, current, prev_close):
    if series is None or series.empty:
        print("No hay datos suficientes para generar el gráfico.")
        return

    is_positive = series.iloc[-1] >= 0
    chart_color = '#00ff41' if is_positive else '#ff3b30' # Verde neón o Rojo
    
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
   
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    ax.plot(series.index, series.values, color=chart_color, linewidth=1.5)
    ax.fill_between(series.index, series.values, 0, color=chart_color, alpha=0.1)
    
    ax.axhline(0, color='white', linestyle='--', linewidth=0.8, alpha=0.5)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(color='gray', fontsize=16)
    plt.yticks(color='gray', fontsize=16)
    
    change_symbol = "+" if is_positive else ""
    pct_val = series.iloc[-1]
    
    plt.title(f"${current:,.2f}", fontsize=20, fontweight='bold', color='white', loc='center', pad=20)
    
    plt.text(series.index[0], series.max() * 0.95 if is_positive else series.min() * 0.95, 
             f"{change_symbol}{pct_val:.2f}%", 
             fontsize=14, color=chart_color, fontweight='bold')

    ax.scatter(series.index[-1], series.iloc[-1], color='white', s=40, zorder=5)
    
    plt.grid(visible=True, linestyle=':', alpha=0.2, color='gray')
    plt.tight_layout()
    
    nombre_archivo = 'holdings.png'
    ruta = os.path.join("/home/diego/scripts/grafstoncks/", nombre_archivo)
    
    with open("/home/diego/scripts/grafstoncks/pct.txt", "w") as f:
        f.write(f"{change_symbol}{pct_val:,.2f}%\n${current:,.2f}")
    
    plt.savefig(ruta, dpi=300, bbox_inches='tight', transparent=True)
    
    ruta_completa = os.path.abspath(nombre_archivo)
    print(f"✅ Imagen guardada exitosamente en: {ruta_completa}")
    
    plt.close()

if __name__ == "__main__":
    pct_series, current_val, prev_close_val = get_portfolio_performance(portfolio_positions, cash)
    plot_and_save_chart(pct_series, current_val, prev_close_val)
    print("--- Proceso finalizado ---")
