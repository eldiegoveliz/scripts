import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import os # Importamos os para mostrar la ruta de guardado

# ==========================================
# 1. CONFIGURACIÓN DE LA CARTERA
# ==========================================

portfolio_positions = {
    "SRPT": 7,
    "GOVZ": 20,
    "SLNO": 3,
    "ABVX": 3.1798,



    "QCLS": 2,

}


cash = 22.73

# ==========================================
# 2. OBTENCIÓN Y PROCESAMIENTO DE DATOS
# ==========================================
def get_portfolio_performance(positions, cash_holdings):
    tickers = list(positions.keys())
    
    print("--- Iniciando proceso ---")
    print(f"Obteniendo datos de: {', '.join(tickers)}")
    # Descargar datos: 1 día, intervalo 1 minuto, incluyendo pre/post market
    try:
        df = yf.download(tickers, period="1d", interval="1m", prepost=True, progress=False)['Close']
    except Exception as e:
        print(f"Error descargando datos: {e}")
        return None, None, None

    # Manejo si solo hay una acción (la estructura de datos cambia)
    if len(tickers) == 1:
        df = df.to_frame(name=tickers[0])
        
    # Rellenar huecos (forward fill) para mantener la continuidad en pre/post market
    df = df.ffill().bfill()
    
    # Calcular el valor previo de cierre (para el % de cambio)
    total_prev_close = cash_holdings
    
    print("Calculando cierre anterior...")
    for ticker in tickers:
        try:
            # Intentamos obtener el cierre anterior oficial de los metadatos
            ticker_obj = yf.Ticker(ticker)
            # Usamos 'regularMarketPreviousClose' que suele ser más estable
            prev = ticker_obj.info.get('regularMarketPreviousClose', df[ticker].iloc[0])
            total_prev_close += prev * positions[ticker]
        except Exception as e:
            print(f"Aviso: No se pudo obtener previousClose para {ticker}, usando primer dato del día. Error: {e}")
            total_prev_close += df[ticker].iloc[0] * positions[ticker]

    # Calcular la serie de tiempo del valor total de la cartera
    portfolio_value = pd.Series(cash_holdings, index=df.index)
    for ticker, qty in positions.items():
        portfolio_value += df[ticker] * qty
        
    # Calcular cambio porcentual diario respecto al cierre de ayer
    pct_change = ((portfolio_value - total_prev_close) / total_prev_close) * 100
    
    return pct_change, portfolio_value.iloc[-1], total_prev_close

# ==========================================
# 3. GENERACIÓN Y GUARDADO DEL GRÁFICO
# ==========================================
def plot_and_save_chart(series, current, prev_close):
    if series is None or series.empty:
        print("No hay datos suficientes para generar el gráfico.")
        return

    # Determinar color basado en si estamos ganando o perdiendo hoy
    is_positive = series.iloc[-1] >= 0
    chart_color = '#00ff41' if is_positive else '#ff3b30' # Verde neón o Rojo
    
    # Configuración de estilo oscuro
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Quitar bordes innecesarios (Spines)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    # Graficar la línea
    ax.plot(series.index, series.values, color=chart_color, linewidth=1.5)
    
    # Relleno bajo la curva (gradiente sutil simulado con alpha bajo)
    ax.fill_between(series.index, series.values, 0, color=chart_color, alpha=0.1)
    
    # Línea base (0%)
    ax.axhline(0, color='white', linestyle='--', linewidth=0.8, alpha=0.5)
    
    # Formato de fechas en eje X (Hora)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(color='gray', fontsize=16)
    plt.yticks(color='gray', fontsize=16)
    
    # Títulos y Anotaciones Dinámicas
    change_symbol = "+" if is_positive else ""
    pct_val = series.iloc[-1]
    
    # Título Principal (Valor Actual Total)
    plt.title(f"${current:,.2f}", fontsize=20, fontweight='bold', color='white', loc='center', pad=20)
    
    # Subtítulo (Cambio Porcentual vs Cierre Ayer)
    # Lo colocamos arriba a la izquierda, debajo del título
    plt.text(series.index[0], series.max() * 0.95 if is_positive else series.min() * 0.95, 
             f"{change_symbol}{pct_val:.2f}%", 
             fontsize=14, color=chart_color, fontweight='bold')

    # Añadir punto blanco al final de la línea actual
    ax.scatter(series.index[-1], series.iloc[-1], color='white', s=40, zorder=5)
    
    plt.grid(visible=True, linestyle=':', alpha=0.2, color='gray')
    plt.tight_layout()
    
    # --- SECCIÓN DE GUARDADO ---
    nombre_archivo = 'holdings.png'
    ruta = os.path.join("/home/diego/scripts/grafstoncks/", nombre_archivo)
    
    # archivo de texto para waybar
    with open("/home/diego/scripts/grafstoncks/pct.txt", "w") as f:
        f.write(f"{change_symbol}{pct_val:,.2f}%\n${current:,.2f}")
    
    # Guardamos la imagen en alta resolución (dpi=300) y ajustada (bbox_inches='tight')
    plt.savefig(ruta, dpi=300, bbox_inches='tight', transparent=True)
    
    ruta_completa = os.path.abspath(nombre_archivo)
    print(f"✅ Imagen guardada exitosamente en: {ruta_completa}")
    
    # Opcional: Comenta la siguiente línea si NO quieres que se abra la ventana del gráfico
    # plt.show() 
    plt.close() # Cierra la figura para liberar memoria

# ==========================================
# EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    # 1. Ejecutar cálculos
    pct_series, current_val, prev_close_val = get_portfolio_performance(portfolio_positions, cash)

    # 2. Generar y guardar
    plot_and_save_chart(pct_series, current_val, prev_close_val)
    print("--- Proceso finalizado ---")
