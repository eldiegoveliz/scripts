import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE USUARIO
# ==========================================

MI_CARTERA = {
    "AAPL": 10,          # Apple (USD)
    "MSFT": 5,           # Microsoft (USD)
    "TSLA": 8,           # Tesla (USD)
    "CHILE.SN": 5000,    # Banco de Chile (CLP)
    "COPEC.SN": 200,     # Copec (CLP)
    "CENCOSUD.SN": 300   # Cencosud (CLP)
}

# Elige la moneda en la que quieres ver el TOTAL y el gráfico
# Opciones: 'USD' o 'CLP'
TARGET_CURRENCY = 'USD' 

# ==========================================
# LÓGICA DE DATOS
# ==========================================

def obtener_datos_cartera(cartera, moneda_objetivo='USD'):
    """
    Descarga datos, maneja fallos en divisas y calcula el valor total.
    """
    print(f"--- Iniciando descarga de datos (Objetivo: {moneda_objetivo}) ---")
    
    tickers = list(cartera.keys())
    
    # 1. Descargar datos de acciones PRIMERO para tener un índice de tiempo fiable
    print(f"Descargando acciones: {', '.join(tickers)}...")
    datos_stocks = yf.download(tickers, period="1d", interval="5m", group_by='ticker', progress=False)

    if datos_stocks.empty:
        raise ValueError("No se obtuvieron datos de acciones. El mercado puede estar cerrado.")

    # Determinar el índice maestro (usamos el índice de la primera acción válida)
    # Esto define el eje X del gráfico
    idx_ref = None
    if len(tickers) > 1:
        # Buscar el primer ticker que tenga datos
        for t in tickers:
            if t in datos_stocks and not datos_stocks[t].empty:
                idx_ref = datos_stocks[t].index
                break
    else:
        idx_ref = datos_stocks.index

    if idx_ref is None:
        raise ValueError("Datos vacíos para todos los tickers.")

    # Normalizar zona horaria del índice maestro
    idx_ref = idx_ref.tz_convert(None)
    
    # 2. Obtener Tipo de Cambio (con manejo de errores robusto)
    print("Obteniendo tipo de cambio USD/CLP...")
    serie_tasa_cambio = None
    usar_tasa_fija = False
    
    try:
        usd_clp_ticker = yf.Ticker("CLP=X")
        df_forex = usd_clp_ticker.history(period="1d", interval="5m")
        
        if df_forex.empty:
            print("! Advertencia: Datos intradía del dólar vacíos. Intentando obtener último precio...")
            usar_tasa_fija = True
        else:
            # Limpiar zona horaria y reindexar al índice de las acciones
            df_forex.index = df_forex.index.tz_convert(None)
            serie_tasa_cambio = df_forex['Close'].reindex(idx_ref, method='ffill').fillna(method='bfill')
            
    except Exception as e:
        print(f"! Error obteniendo historial del dólar: {e}")
        usar_tasa_fija = True

    # FALLBACK: Si falló la serie de tiempo del dólar, usar un valor fijo
    if usar_tasa_fija or serie_tasa_cambio is None:
        try:
            # Intentamos obtener el último dato de 5 días para asegurar un cierre
            hist_5d = yf.Ticker("CLP=X").history(period="5d")
            if not hist_5d.empty:
                ultimo_precio = hist_5d['Close'].iloc[-1]
                print(f"-> Usando tasa de cambio fija (último cierre): ${ultimo_precio:.2f}")
                # Crear una serie constante con el mismo índice que las acciones
                serie_tasa_cambio = pd.Series(ultimo_precio, index=idx_ref)
            else:
                raise ValueError("No se pudo obtener ninguna tasa de cambio para CLP=X")
        except Exception as ex:
            raise ValueError(f"Fallo crítico obteniendo dólar: {ex}")

    # 3. Calcular Valor de la Cartera
    df_total = pd.DataFrame(index=idx_ref)

    for ticker, cantidad in cartera.items():
        # Extraer serie de precios
        if len(tickers) > 1:
            if ticker not in datos_stocks: 
                continue
            serie_precio = datos_stocks[ticker]['Close']
        else:
            serie_precio = datos_stocks['Close']

        # Limpieza de índice
        serie_precio.index = serie_precio.index.tz_convert(None)
        
        # Alinear exactamente al índice maestro
        serie_precio = serie_precio.reindex(idx_ref, method='ffill')
        
        valor_bruto = serie_precio * cantidad
        
        # Conversión
        es_chilena = ticker.endswith('.SN')
        valor_neto = None
        
        if moneda_objetivo == 'USD':
            if es_chilena:
                valor_neto = valor_bruto / serie_tasa_cambio
            else:
                valor_neto = valor_bruto
        elif moneda_objetivo == 'CLP':
            if es_chilena:
                valor_neto = valor_bruto
            else:
                valor_neto = valor_bruto * serie_tasa_cambio
        
        df_total[ticker] = valor_neto

    # Limpiar NaN iniciales
    df_total = df_total.dropna()
    
    if df_total.empty:
        raise ValueError("El cruce de datos resultó en un DataFrame vacío (posible desalineación de horarios).")

    df_total['Total_Portfolio'] = df_total.sum(axis=1)
    
    return df_total['Total_Portfolio']

# ==========================================
# GRAFICACIÓN MINIMALISTA
# ==========================================

def graficar_rendimiento(serie_valor, moneda):
    if serie_valor.empty:
        print("No hay datos suficientes para graficar.")
        return

    # Cálculos finales
    valor_apertura = serie_valor.iloc[0]
    valor_actual = serie_valor.iloc[-1]
    diff = valor_actual - valor_apertura
    pct_change = (diff / valor_apertura) * 100
    
    # Configuración de colores
    color_linea = '#2563EB' 
    color_positivo = '#16A34A' 
    color_negativo = '#DC2626' 
    color_texto = '#374151' 
    
    color_cambio = color_positivo if diff >= 0 else color_negativo
    simbolo = "+" if diff >= 0 else ""
    
    # Crear figura
    fig, ax = plt.figure(figsize=(10, 6), facecolor='white'), plt.gca()
    
    # Graficar línea
    ax.plot(serie_valor.index, serie_valor.values, color=color_linea, linewidth=2.5)
    
    ax.fill_between(serie_valor.index, serie_valor.values, valor_apertura, 
                    alpha=0.1, color=color_linea)

    ax.axhline(y=valor_apertura, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#E5E7EB')
    ax.spines['bottom'].set_color('#E5E7EB')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    moneda_symbol = "$" if moneda == "CLP" else "US$"
    
    plt.suptitle(f"{moneda_symbol} {valor_actual:,.2f}", 
                 fontsize=26, fontweight='bold', color=color_texto, x=0.125, ha='left')
    
    plt.title(f"Rendimiento Diario: {simbolo}{diff:,.2f} ({simbolo}{pct_change:.2f}%)", 
              fontsize=14, color=color_cambio, loc='left', pad=10)
    
    plt.xlabel('Hora', fontsize=10, color='gray')
    plt.grid(True, which='major', axis='y', linestyle=':', alpha=0.3)
    
    ax.scatter(serie_valor.index[-1], valor_actual, color=color_linea, s=50, zorder=5)

    plt.tight_layout(rect=[0, 0.03, 1, 0.90])
    
    print("\nGenerando gráfico...")
    plt.show()

# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    try:
        serie_portfolio = obtener_datos_cartera(MI_CARTERA, TARGET_CURRENCY)
        graficar_rendimiento(serie_portfolio, TARGET_CURRENCY)
    except Exception as e:
        print(f"Ocurrió un error: {e}")
