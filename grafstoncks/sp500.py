import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import os

def generar_grafica_sp500():
    # 1. Configuración y Descarga de datos
    # El ticker del IPSA en Yahoo Finance es standardmente '^IPSA'
    ticker = "^GSPC"



    print(f"Descargando datos para {ticker}...")
    # Intervalo de 5m o 1m para tener detalle intradía
    data = yf.download(ticker, period="1d", interval="1m", progress=False)

    if data.empty:
        print("No hay datos disponibles (¿El mercado está cerrado o es muy temprano?).")
        return

    # 2. Preparación de datos
    # Usamos el precio de cierre de cada intervalo
    precios = data['Close'].values.flatten() # Flatten para asegurar 1D array
    
    # La referencia es el primer precio de la sesión (Apertura)
    precio_apertura = precios[0] 
    
    # Crear un array de índices para el eje X (0, 1, 2...)
    x = np.arange(len(precios))

    # 3. Lógica de Colores (Segmentación)
    # Para cambiar de color, necesitamos dividir la línea en segmentos.
    # Un segmento va del punto i al punto i+1.
    points = np.array([x, precios]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)

    # Definir colores: Verde si el segmento está sobre la apertura, Rojo si está bajo.
    # Usamos el promedio del segmento para decidir el color
    colors = []
    for i in range(len(precios) - 1):
        # Promedio del punto actual y el siguiente
        avg_segmento = (precios[i] + precios[i+1]) / 2
        if avg_segmento >= precio_apertura:
            colors.append('#00C805') # Verde "Trading" brillante
        else:
            colors.append('#FF3B30') # Rojo "Trading" brillante
    # Precio actual
    stock = yf.Ticker(ticker)
    cp = stock.info["regularMarketPrice"]   

    # 4. Graficar
    fig, ax = plt.subplots(figsize=(5, 2)) # Formato ancho

    # Crear la colección de líneas con los colores calculados
    lc = LineCollection(segments, colors=colors, linewidths=1)
    ax.add_collection(lc)

    # Ajustar los límites del gráfico
    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(precios.min(), precios.max())
    
    # Opcional: Añadir una línea punteada muy sutil en el precio de apertura (eje 0%)
    # ax.axhline(y=precio_apertura, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)

    ax.text(0.02, -0.1, f"S&P500", transform=ax.transAxes, color="white", 
    fontsize=12, ha="left", va="top")
    ax.text(0.98, -0.1, f"{cp}", transform=ax.transAxes, color="white", 
    fontsize=12, ha="right", va="top")


    # 5. Estilo Minimalista (Borrar todo excepto la línea)
    ax.axis('off')           # Apagar ejes
    ax.set_frame_on(False)   # Quitar el marco
    
    # Eliminar márgenes blancos extras
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

    # 6. Guardar
    nombre_archivo = "sp500.png"
    ruta=os.path.join("/home/diego/scripts/grafstoncks/", nombre_archivo)
    plt.savefig(ruta, transparent=True, dpi=100, bbox_inches='tight', pad_inches=0)
    plt.close()
    
    print(f"Gráfica generada exitosamente: {nombre_archivo}")

if __name__ == "__main__":
    generar_grafica_sp500()
