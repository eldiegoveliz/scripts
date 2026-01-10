import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import os

# ==========================================
# CONFIGURACIÓN DE USUARIO
# ==========================================

MI_CARTERA = {
    "TIP": 1.4534,          # Stock (USD)
    "SRPT": 8,           
    "IONZ": 36,          
    "SPRB": 1,
    "TLT": 1,
    "GOOG": 0.2,
    "RGTZ": 2,
    "BHVN":8,
    "ABVX": 0.6521,
    "PLTR":0.12,
#    "BTG": 0,
#    "QURE": 0,
    "BLNE": 2,
    "NVDA": 0.0151
#    "CHILE.SN": 566,    # Banco de Chile (CLP)
#    "BCI.SN": 2,     # Copec (CLP)
#    "BSANTANDER.SN": 604,   # Cencosud (CLP)
    
#    "USD": 34.16
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
    datos_stocks = yf.download(tickers, period="1d", interval="2m", group_by='ticker', progress=False)

    if datos_stocks.empty:
        raise ValueError("No se obtuvieron datos de acciones. El mercado puede estar cerrado.")

    # Determinar el índice maestro (usamos el índice de la primera acción válida)
    # Esto define el eje X del gráfico
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

    # Normalizar zona horaria del índice maestro
    idx_ref = idx_ref.tz_convert("US/Eastern")
    
    # 2. Obtener Tipo de Cambio (con manejo de errores robusto)
    print("Obteniendo tipo de cambio USD/CLP...")
    serie_tasa_cambio = None
    usar_tasa_fija = False
    
    try:
        usd_clp_ticker = yf.Ticker("CLP=X")
        # CAMBIO: Intervalo 1m también para el dólar
        df_forex = usd_clp_ticker.history(period="1d", interval="2m")
        
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
        serie_precio.index = serie_precio.index.tz_convert("US/Eastern")
        
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
    fig, ax = plt.figure(figsize=(5, 2)), plt.gca()
    
    # Graficar línea
    ax.plot(serie_valor.index, serie_valor.values, color=color_linea, linewidth=1.1)
    
    # Relleno suave bajo la línea (efecto moderno)
    ax.fill_between(serie_valor.index, serie_valor.values, valor_apertura, 
                    alpha=0.1, color=color_linea)

    # Línea de referencia (Apertura)
    # ax.axhline(y=valor_apertura, color='gray', linestyle='--', alpha=0.5, linewidth=1)
    
    # --- ESTILOS ULTRA MINIMALISTAS ---
    # Eliminar ejes, bordes y etiquetas por completo
    ax.set_axis_off()
    
    # Títulos dinámicos
    moneda_symbol = "$" if moneda == "CLP" else "US$"
    
    # Título Principal (Valor Total)
    plt.suptitle(f"{moneda_symbol} {valor_actual:,.2f}", 
                 fontsize=12, fontweight='bold', color="white", x=0.5, y=0.8, ha='center')
    
    # Subtítulo (Cambio Porcentual)
    #plt.title(f"{simbolo}{diff:,.2f} ({simbolo}{pct_change:.2f}%)", 
    #         fontsize=12, color=color_cambio, loc='left', pad=4, x=-0.01)
    ax.text(0.98, -0.1, f"{simbolo}{diff:,.2f} ({simbolo}{pct_change:.2f}%)", transform=ax.transAxes, color="white", fontsize=12, ha="right", va="top")    
    ax.text(0.02, -0.1, f"Holdings", transform=ax.transAxes, color="white", fontsize=12, ha="left", va="top")    


    # Mostrar último punto
    ax.scatter(serie_valor.index[-1], valor_actual, color=color_linea, s=80, zorder=5)

    #plt.tight_layout(rect=[0, 0, 1, 0.85]) # Ajustar márgenes para que el título grande respire
    
    print("\nGenerando gráfico...")
    
    # GUARDAR EN ARCHIVO (Solución al error non-interactive)
    directorio = os.path.dirname(os.path.abspath(__file__))
    nombre_archivo = "holdings.png"
    ruta = os.path.join("/home/diego/scripts/grafstoncks/", nombre_archivo)
    
    # bbox_inches='tight' recorta el espacio blanco extra
    plt.savefig(ruta, transparent=True, dpi=100, bbox_inches='tight', pad_inches=0) 
    print(f"Gráfico guardado exitosamente como: {nombre_archivo}")
    
    # Intentar mostrar en ventana (si el entorno lo permite)
    #try:
    #    plt.show()
    #except Exception:
    #    pass

# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":
    try:
        serie_portfolio = obtener_datos_cartera(MI_CARTERA, TARGET_CURRENCY)
        graficar_rendimiento(serie_portfolio, TARGET_CURRENCY)
    except Exception as e:
        print(f"Ocurrió un error: {e}")
