import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os  # <-- Nueva importación para manejar rutas

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

# NUEVO: Configuración de Efectivo / Caja
# Ingresa aquí el dinero líquido que quieres sumar al patrimonio
MI_CASH = {
    "USD": 1200,     # Dólares en efectivo/cuenta
    "CLP": 500000    # Pesos chilenos en efectivo/cuenta
}

# Elige la moneda en la que quieres ver el TOTAL y el gráfico
# Opciones: 'USD' o 'CLP'
TARGET_CURRENCY = 'USD' 

# ==========================================
# LÓGICA DE DATOS
# ==========================================

def obtener_datos_cartera(cartera, cash, moneda_objetivo='USD'):
    """
    Descarga datos, maneja acciones y efectivo, y calcula el valor total.
    """
    print(f"--- Iniciando descarga de datos (Objetivo: {moneda_objetivo}) ---")
    
    tickers = list(cartera.keys())
    
    # 1. Descargar datos de acciones PRIMERO
    print(f"Descargando acciones: {', '.join(tickers)}...")
    # CAMBIO: Intervalo a 1m para máxima precisión
    datos_stocks = yf.download(tickers, period="1d", interval="1m", group_by='ticker', progress=False)

    if datos_stocks.empty:
        raise ValueError("No se obtuvieron datos de acciones. El mercado puede estar cerrado.")

    # Determinar el índice maestro (Eje de tiempo)
    # MEJORA: Buscar el ticker con MÁS datos para usarlo como referencia de tiempo
    # Esto evita que una acción ilíquida (con pocos datos) acorte el gráfico
    idx_ref = None
    max_len = 0
    
    if len(tickers) > 1:
        for t in tickers:
            if t in datos_stocks and not datos_stocks[t].empty:
                current_len = len(datos_stocks[t])
                if current_len > max_len:
                    max_len = current_len
                    idx_ref = datos_stocks[t].index
    else:
        idx_ref = datos_stocks.index

    if idx_ref is None:
        raise ValueError("Datos vacíos para todos los tickers.")

    # Convertir a zona horaria de NASDAQ (US/Eastern)
    idx_ref = idx_ref.tz_convert('US/Eastern')
    
    # 2. Obtener Tipo de Cambio (con manejo de errores robusto)
    print("Obteniendo tipo de cambio USD/CLP...")
    serie_tasa_cambio = None
    usar_tasa_fija = False
    
    try:
        usd_clp_ticker = yf.Ticker("CLP=X")
        # CAMBIO: Intervalo 1m también para el dólar
        df_forex = usd_clp_ticker.history(period="1d", interval="1m")
        
        if df_forex.empty:
            print("! Advertencia: Datos intradía del dólar vacíos. Intentando obtener último precio...")
            usar_tasa_fija = True
        else:
            df_forex.index = df_forex.index.tz_convert('US/Eastern')
            # Rellenar huecos del dólar si faltan minutos
            serie_tasa_cambio = df_forex['Close'].reindex(idx_ref, method='ffill').fillna(method='bfill')
            
    except Exception as e:
        print(f"! Error obteniendo historial del dólar: {e}")
        usar_tasa_fija = True

    # FALLBACK Tasa de cambio
    if usar_tasa_fija or serie_tasa_cambio is None:
        try:
            hist_5d = yf.Ticker("CLP=X").history(period="5d")
            if not hist_5d.empty:
                ultimo_precio = hist_5d['Close'].iloc[-1]
                print(f"-> Usando tasa de cambio fija (último cierre): ${ultimo_precio:.2f}")
                serie_tasa_cambio = pd.Series(ultimo_precio, index=idx_ref)
            else:
                raise ValueError("No se pudo obtener ninguna tasa de cambio para CLP=X")
        except Exception as ex:
            raise ValueError(f"Fallo crítico obteniendo dólar: {ex}")

    # 3. Calcular Valor de la Cartera (Acciones + Efectivo)
    df_total = pd.DataFrame(index=idx_ref)

    # A) Procesar Acciones
    for ticker, cantidad in cartera.items():
        if len(tickers) > 1:
            if ticker not in datos_stocks: continue
            serie_precio = datos_stocks[ticker]['Close']
        else:
            serie_precio = datos_stocks['Close']

        serie_precio.index = serie_precio.index.tz_convert('US/Eastern')
        
        # IMPORTANTE: Reindex con 'ffill' rellena los minutos vacíos con el último precio conocido
        # Esto soluciona el problema de las acciones chilenas ilíquidas en gráficos de 1m
        serie_precio = serie_precio.reindex(idx_ref, method='ffill')
        
        valor_bruto = serie_precio * cantidad
        es_chilena = ticker.endswith('.SN')
        valor_neto = None
        
        if moneda_objetivo == 'USD':
            if es_chilena: valor_neto = valor_bruto / serie_tasa_cambio
            else: valor_neto = valor_bruto
        elif moneda_objetivo == 'CLP':
            if es_chilena: valor_neto = valor_bruto
            else: valor_neto = valor_bruto * serie_tasa_cambio
        
        df_total[ticker] = valor_neto

    # B) Procesar Efectivo (CASH)
    print("Integrando efectivo...")
    for moneda_cash, monto in cash.items():
        if monto == 0: continue
        
        valor_cash_convertido = 0
        col_name = f"CASH_{moneda_cash}"
        
        if moneda_objetivo == 'USD':
            if moneda_cash == 'CLP':
                # Convertir CLP estáticos a USD dinámicos (dividido por tasa variable)
                valor_cash_convertido = monto / serie_tasa_cambio
            else: # USD
                valor_cash_convertido = monto
                
        elif moneda_objetivo == 'CLP':
            if moneda_cash == 'USD':
                # Convertir USD estáticos a CLP dinámicos (multiplicado por tasa variable)
                valor_cash_convertido = monto * serie_tasa_cambio
            else: # CLP
                valor_cash_convertido = monto

        df_total[col_name] = valor_cash_convertido

    # Limpiar y Sumar
    df_total = df_total.dropna()
    
    if df_total.empty:
        raise ValueError("El DataFrame final está vacío.")

    df_total['Total_Portfolio'] = df_total.sum(axis=1)
    
    return df_total['Total_Portfolio']

# ==========================================
# GRAFICACIÓN MINIMALISTA
# ==========================================

def graficar_rendimiento(serie_valor, moneda):
    if serie_valor.empty:
        print("No hay datos suficientes para graficar.")
        return

    valor_apertura = serie_valor.iloc[0]
    valor_actual = serie_valor.iloc[-1]
    diff = valor_actual - valor_apertura
    pct_change = (diff / valor_apertura) * 100
    
    color_linea = '#2563EB' 
    color_positivo = '#16A34A' 
    color_negativo = '#DC2626' 
    color_texto = '#374151' 
    
    color_cambio = color_positivo if diff >= 0 else color_negativo
    simbolo = "+" if diff >= 0 else ""
    
    fig, ax = plt.figure(figsize=(10, 6), facecolor='white'), plt.gca()
    
    ax.plot(serie_valor.index, serie_valor.values, color=color_linea, linewidth=2.5)
    
    ax.fill_between(serie_valor.index, serie_valor.values, valor_apertura, 
                    alpha=0.1, color=color_linea)

    ax.axhline(y=valor_apertura, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    ax.set_axis_off()
    
    moneda_symbol = "$" if moneda == "CLP" else "US$"
    
    plt.suptitle(f"{moneda_symbol} {valor_actual:,.2f}", 
                 fontsize=40, fontweight='bold', color=color_texto, x=0.05, ha='left')
    
    plt.title(f"Rendimiento Diario: {simbolo}{diff:,.2f} ({simbolo}{pct_change:.2f}%)", 
              fontsize=18, color=color_cambio, loc='left', pad=4, x=-0.01)
    
    ax.scatter(serie_valor.index[-1], valor_actual, color=color_linea, s=80, zorder=5)

    plt.tight_layout(rect=[0, 0, 1, 0.85])
    
    print("\nGenerando gráfico...")
    
    # MODIFICACIÓN: Guardar en el directorio del script
    # Obtiene la ruta de la carpeta donde vive este archivo .py
    directorio_script = os.path.dirname(os.path.abspath(__file__))
    nombre_archivo = "mi_cartera.png"
    ruta_completa = os.path.join(directorio_script, nombre_archivo)
    
    plt.savefig(ruta_completa, dpi=150, bbox_inches='tight', pad_inches=0.5) 
    print(f"✅ Gráfico guardado exitosamente en: {ruta_completa}")
    
    try:
        plt.show()
    except Exception:
        pass

# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    try:
        # Pasamos MI_CASH a la función
        serie_portfolio = obtener_datos_cartera(MI_CARTERA, MI_CASH, TARGET_CURRENCY)
        graficar_rendimiento(serie_portfolio, TARGET_CURRENCY)
    except Exception as e:
        print(f"Ocurrió un error: {e}")
