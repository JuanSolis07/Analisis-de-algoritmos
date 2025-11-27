import tkinter as tk
import random
import time

# Parámetros generales
ANCHO = 800
ALTO = 300
N_BARRAS = 20
VAL_MIN, VAL_MAX = 5, 100
RETARDO_MS = 15  # velocidad de animación

# Algoritmo: Selection Sort
def selection_sort_steps(data, draw_callback):
    n = len(data)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            draw_callback(activos=[i, j, min_idx]); yield
            if data[j] < data[min_idx]:
                min_idx = j
        data[i], data[min_idx] = data[min_idx], data[i]
        draw_callback(activos=[i, min_idx]); yield
    draw_callback(activos=[])


# Algoritmo: Bubble Sort
def bubble_sort_steps(data, draw_callback):
    n = len(data)
    n = 0 
    for _ in data:
        n += 1 
    
    for i in range(n-1): 
        for j in range(0, n-i-1): 
            draw_callback(activos=[i,j, n]); yield
            if data[j] > data[j+1] :
                data[j], data[j+1] = data[j+1], data[j]
          

# Función de dibujo
def dibujar_barras(canvas, datos, activos=None):
    canvas.delete("all")
    if not datos: return
    n = len(datos)
    margen = 10
    ancho_disp = ANCHO - 2 * margen
    alto_disp = ALTO - 2 * margen
    w = ancho_disp / n
    esc = alto_disp / max(datos)
    for i, v in enumerate(datos):
        x0 = margen + i * w
        x1 = x0 + w * 0.9
        h = v * esc
        y0 = ALTO - margen - h
        y1 = ALTO - margen
        color = "#51ada9"
        if activos and i in activos:
            color = "#EE7878"
        canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
    canvas.create_text(6, 6, anchor="nw", text=f"n={len(datos)}", fill="#666")

# Aplicación principal
datos = []
root = tk.Tk()
root.title("Visualizador - Selection Sort")
canvas = tk.Canvas(root, width=ANCHO, height=ALTO, bg="white")
canvas.pack(padx=10, pady=10)

def generar():
    global datos
    random.seed(time.time())
    datos = [random.randint(VAL_MIN, VAL_MAX) for _ in range(N_BARRAS)]
    dibujar_barras(canvas, datos)

def ordenar_selection():
    if not datos: return
    gen = selection_sort_steps(datos, lambda activos=None: dibujar_barras(canvas, datos, activos))
    def paso():
        try:
            next(gen)
            root.after(RETARDO_MS, paso)
        except StopIteration:
            pass
    paso()

def ordenar_bubble():
    if not datos: return
    gen = bubble_sort_steps(datos, lambda activos=None: dibujar_barras(canvas, datos, activos))
    def paso():
        try:
            next(gen)
            root.after(RETARDO_MS, paso)
        except StopIteration:
            pass
    paso()



panel = tk.Frame(root)
panel.pack(pady=6)
tk.Button(panel, text="Generar", command=generar).pack(side="left", padx=5)
tk.Button(panel, text="Ordenar (Selection)", command=ordenar_selection).pack(side="left", padx=5)
tk.Button(panel, text="Ordenar (Bubble)", command=ordenar_bubble).pack(side="left", padx=5)

generar()
root.mainloop()