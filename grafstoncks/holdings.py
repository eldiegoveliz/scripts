import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
portfolio_data = [
    {'ticker': 'AAPL', 'qty': 10},        # Apple (NASDAQ)
    {'ticker': 'MSFT', 'qty': 5},         # Microsoft (NASDAQ)
    {'ticker': 'SQM-B.SN', 'qty': 100},   # SQM Serie B (Santiago)
    {'ticker': 'CHILE.SN', 'qty': 500},   # Banco de Chile
    {'ticker': 'COPEC.SN', 'qty': 200},   # Copec
    {'ticker': 'NVDA', 'qty': 2}          # Nvidia
]

# ==========================================
# 2. LÓGICA DE DATOS
# ==========================================

def get_exchange_rate():
    """Obtiene el precio del dólar (USD) en pesos (CLP)."""
    try:
        ticker = yf.Ticker("CLP=X")
        hist = ticker.history(period="1d")
        if not hist.empty:
            rate = hist['Close'].iloc[-1]
            return rate
        return 950.0 
    except Exception:
        return 950.0

def get_portfolio_data(portfolio, usd_clp_rate):
    """Calcula totales y detalles normalizados a USD."""
    total_current_usd = 0
    total_open_usd = 0
    details = []

    print(f"--- Procesando datos (Dólar: ${usd_clp_rate:.2f}) ---")

    for item in portfolio:
        symbol = item['ticker']
        qty = item['qty']
        
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            
            if hist.empty:
                continue

            current_price = hist['Close'].iloc[-1]
            open_price = hist['Open'].iloc[0]
            
            # Detectar moneda
            info = stock.info
            # A veces la API no trae 'currency', asumimos USD si falla, o CLP si termina en .SN
            currency = info.get('currency', 'CLP' if '.SN' in symbol else 'USD')
            
            # Normalización
            if currency == 'CLP':
                val_usd_now = (current_price * qty) / usd_clp_rate
                val_usd_open = (open_price * qty) / usd_clp_rate
                display_currency = "CLP"
            else:
                val_usd_now = current_price * qty
                val_usd_open = open_price * qty
                display_currency = "USD"

            total_current_usd += val_usd_now
            total_open_usd += val_usd_open
            
            details.append({
                'Ticker': symbol,
                'Value_USD': val_usd_now
            })
            print(f"OK: {symbol}")

        except Exception as e:
            print(f"Error en {symbol}: {e}")

    return total_current_usd, total_open_usd, details

# ==========================================
# 3. GENERACIÓN DE GRÁFICO Y GUARDADO (OS)
# ==========================================

def create_and_save_chart(total_usd, total_open_usd, rate, details):
    # Cálculos
    total_clp = total_usd * rate
    pct_change = 0
    if total_open_usd > 0:
        pct_change = ((total_usd - total_open_usd) / total_open_usd) * 100
    
    change_color = '#4caf50' if pct_change >= 0 else '#d32f2f'
    symbol_sign = '+' if pct_change >= 0 else ''

    # Configuración Figura
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('white')
    ax.axis('off')

    # Textos Principales
    plt.text(0.5, 0.95, 'ESTADO DEL PORTAFOLIO', 
             ha='center', va='center', fontsize=12, color='gray', weight='bold')

    plt.text(0.5, 0.85, f"USD {total_usd:,.2f}", 
             ha='center', va='center', fontsize=35, color='#212121', weight='bold')

    plt.text(0.5, 0.78, f"CLP ${total_clp:,.0f}", 
             ha='center', va='center', fontsize=16, color='#757575')

    plt.text(0.5, 0.70, f"{symbol_sign}{pct_change:.2f}% Hoy", 
             ha='center', va='center', fontsize=18, color='white', weight='bold',
             bbox=dict(facecolor=change_color, edgecolor='none', boxstyle='round,pad=0.5'))

    # Gráfico de Barras
    df = pd.DataFrame(details).sort_values(by='Value_USD', ascending=True)
    
    # Ejes para las barras [left, bottom, width, height]
    ax_bar = fig.add_axes([0.15, 0.1, 0.7, 0.5]) 
    bars = ax_bar.barh(df['Ticker'], df['Value_USD'], color='#1976d2')
    
    # Limpieza visual
    ax_bar.spines['top'].set_visible(False)
    ax_bar.spines['right'].set_visible(False)
    ax_bar.spines['bottom'].set_visible(False)
    ax_bar.spines['left'].set_visible(False)
    ax_bar.get_xaxis().set_visible(False)
    ax_bar.tick_params(axis='y', length=0, labelsize=10)

    # Etiquetas en barras
    for bar in bars:
        width = bar.get_width()
        ax_bar.text(width + (total_usd * 0.02), bar.get_y() + bar.get_height()/2, 
                    f"${width:,.0f}", 
                    ha='left', va='center', fontsize=9, color='#424242')

    ax_bar.set_title("Composición (en USD)", loc='left', fontsize=10, color='gray')

    # --- USO DE OS PARA GUARDAR ---
    try:
        # Obtener el directorio actual donde se ejecuta el script
        current_dir = os.getcwd()
        
        # Definir nombre del archivo
        filename = "resumen_cartera.png"
        
        # Unir ruta de forma segura segun el sistema operativo
        full_path = os.path.join(current_dir, filename)
        
        # Guardar
        plt.savefig("/home/diego/scripts/grafstoncks/", dpi=150, bbox_inches='tight')
        plt.close() # Importante cerrar para evitar el error de non-interactive
        
        print("\n" + "="*40)
        print("ÉXITO")
        print("="*40)
        print(f"Imagen guardada en:\n{full_path}")
        print("="*40)
        
    except Exception as e:
        print(f"Error guardando el archivo: {e}")

if __name__ == "__main__":
    usd_clp = get_exchange_rate()
    tot_usd, tot_open, data = get_portfolio_data(portfolio_data, usd_clp)
    create_and_save_chart(tot_usd, tot_open, usd_clp, data)
