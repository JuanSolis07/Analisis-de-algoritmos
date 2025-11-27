import tkinter as tk
from tkinter import ttk
import random
import time

ANCHO = 900
ALTO = 300
N_BARRAS = 30  # default
VAL_MIN, VAL_MAX = 5, 100

COLORES_ALGORITMOS = {
    "Selection Sort": "#EE7878",  # Rojo
    "Bubble Sort": "#78EE78",     # Verde
    "Quicksort": "#7878EE",       # Azul
    "MergeSort": "#EE78EE"        # Magenta
}

# Algoritmo: Selection Sort
def selection_sort_steps(data, draw_callback, color):
    n = len(data)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            draw_callback(activos=[i, j, min_idx], color=color)
            yield
            if data[j] < data[min_idx]:
                min_idx = j
        data[i], data[min_idx] = data[min_idx], data[i]
        draw_callback(activos=[i, min_idx], color=color)
        yield
    draw_callback(activos=[], color=color)

# Algoritmo: Bubble Sort
def bubble_sort_steps(data, draw_callback, color):
    n = len(data)
    for i in range(n - 1):
        for j in range(0, n - i - 1):
            draw_callback(activos=[i, j, n], color=color)
            yield
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
                draw_callback(activos=[i, j, n], color=color)
                yield
    draw_callback(activos=[], color=color)

# Algoritmo: Quicksort
def quicksort_steps(data, draw_callback, color):
    def quick(start, end):
        if start < end:
            p = yield from particion(start, end)
            yield from quick(start, p - 1)
            yield from quick(p + 1, end)

    def particion(start, end):
        pivot = data[end]
        i = start - 1
        for j in range(start, end):
            draw_callback(activos=[j, end], color=color)
            yield
            if data[j] <= pivot:
                i += 1
                data[i], data[j] = data[j], data[i]
                draw_callback(activos=[i, j], color=color)
                yield
        data[i + 1], data[end] = data[end], data[i + 1]
        draw_callback(activos=[i + 1, end], color=color)
        yield
        draw_callback(activos=[], color=color)
        yield
        return i + 1

    yield from quick(0, len(data) - 1)

# Algoritmo: MergeSort
def merge_sort_steps(data, draw_callback, color):
    def merge_sort(start, end):
        if start < end:
            mid = (start + end) // 2
            yield from merge_sort(start, mid)
            yield from merge_sort(mid + 1, end)
            yield from merge(start, mid, end)

    def merge(start, mid, end):
        left = data[start:mid + 1]
        right = data[mid + 1:end + 1]
        i = j = 0
        k = start
        
        while i < len(left) and j < len(right):
            draw_callback(activos=[k, start + i, mid + 1 + j], color=color)
            yield
            if left[i] <= right[j]:
                data[k] = left[i]
                i += 1
            else:
                data[k] = right[j]
                j += 1
            k += 1
        
        while i < len(left):
            data[k] = left[i]
            draw_callback(activos=[k, start + i], color=color)
            yield
            i += 1
            k += 1
        
        while j < len(right):
            data[k] = right[j]
            draw_callback(activos=[k, mid + 1 + j], color=color)
            yield
            j += 1
            k += 1
        
        draw_callback(activos=list(range(start, end + 1)), color=color)
        yield

    yield from merge_sort(0, len(data) - 1)
    draw_callback(activos=[], color=color)

# Función de dibujo
def dibujar_barras(canvas, datos, activos=None, color="#EE7878"):
    canvas.delete("all")
    if not datos:
        return
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
        bar_color = "#51ada9"
        if activos and i in activos:
            bar_color = color
        canvas.create_rectangle(x0, y0, x1, y1, fill=bar_color, outline="")
    canvas.create_text(6, 6, anchor="nw", text=f"n={len(datos)}", fill="#666")

# Aplicación principal
datos = []
root = tk.Tk()
root.title("Ordenamiento con Barras")
canvas = tk.Canvas(root, width=ANCHO, height=ALTO, bg="white")
canvas.pack(padx=10, pady=10)

def ordenar():
    if not datos:
        return
    opcion = cb.get()
    color_algoritmo = COLORES_ALGORITMOS.get(opcion, "#EE7878")
    
    if opcion == "Selection Sort":
        gen = selection_sort_steps(datos, lambda activos=None, color=color_algoritmo: dibujar_barras(canvas, datos, activos, color), color_algoritmo)
    elif opcion == "Bubble Sort":
        gen = bubble_sort_steps(datos, lambda activos=None, color=color_algoritmo: dibujar_barras(canvas, datos, activos, color), color_algoritmo)
    elif opcion == "Quicksort":
        gen = quicksort_steps(datos, lambda activos=None, color=color_algoritmo: dibujar_barras(canvas, datos, activos, color), color_algoritmo)
    elif opcion == "MergeSort":
        gen = merge_sort_steps(datos, lambda activos=None, color=color_algoritmo: dibujar_barras(canvas, datos, activos, color), color_algoritmo)
    else:
        return  # nada seleccionado
    
    def paso():
        try:
            next(gen)
            root.after(v1.get(), paso)
        except StopIteration:
            pass
    paso()

def generar():
    global datos
    try:
        n = int(entrada_tam.get())
    except:
        n = N_BARRAS
    random.seed(time.time())
    datos = [random.randint(VAL_MIN, VAL_MAX) for _ in range(n)]
    dibujar_barras(canvas, datos)

def mezclar():
    global datos
    if datos:
        random.shuffle(datos)
        dibujar_barras(canvas, datos)

def limpiar():
    dibujar_barras(canvas, datos)

# Entrada de barras
lbl = tk.Label(root, text="Ingrese el numero de barras: ")
lbl.pack(side='left', pady=5)
entrada_tam = tk.Entry(root, width=5)
entrada_tam.pack(side='left', pady=3)

btn = tk.Button(root, text="Generar datos", command=generar)
btn.pack(side='left', pady=10)

# Dropdown con algoritmos
opciones = ["Selection Sort", "Bubble Sort", "Quicksort", "MergeSort"]
cb = ttk.Combobox(root, values=opciones, state="readonly")
cb.set("Selecciona un algoritmo")
cb.pack(side='left', pady=5)

panel = tk.Frame(root)
panel.pack(side='left', pady=6)
tk.Button(panel, text="Ordenar", command=ordenar).pack(side="left", padx=5)

# Botones adicionales
tk.Button(panel, text="Mezclar", command=mezclar).pack(side="left", padx=5)
tk.Button(panel, text="Limpiar", command=limpiar).pack(side="left", padx=5)

# scale
v1 = tk.IntVar(value=100)
panel_opciones = tk.Frame(root)
panel_opciones.pack(pady=10)

s1 = tk.Scale(panel_opciones, variable=v1, from_=0, to=200, orient="horizontal", label="Velocidad (ms)")
s1.pack(side="left", padx=10)

generar()
root.mainloop()