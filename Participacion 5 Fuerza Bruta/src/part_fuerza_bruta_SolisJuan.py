import tkinter as tk
from tkinter import messagebox
import random
import math

def Distancia(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def calcular():
    puntos = []
    try:
        for i in range(5):
            x = int(entradas[i][0].get())
            y = int(entradas[i][1].get())
            puntos.append((x, y))
    except ValueError:
        messagebox.showerror("Solo se permiten numeros enteros")
        return

    min_dist = float('inf')
    par_cercano = (None, None)

    for i in range(len(puntos)):
        for j in range(i + 1, len(puntos)):
            d = Distancia(puntos[i], puntos[j])
            if d < min_dist:
                min_dist = d
                par_cercano = (puntos[i], puntos[j])

    resultado.config(text=f"Par más cercano: {par_cercano[0]} y {par_cercano[1]}\nDistancia: {min_dist:.2f}")

def llenar():
    for i in range(5):
        x = random.randint(0, 40)
        y = random.randint(0, 40)
        entradas[i][0].delete(0, tk.END)
        entradas[i][1].delete(0, tk.END)
        entradas[i][0].insert(0, str(x))
        entradas[i][1].insert(0, str(y))

def limpiar():
    for i in range(5):
        entradas[i][0].delete(0, tk.END)
        entradas[i][1].delete(0, tk.END)
    resultado.config(text="")

ventana = tk.Tk()
ventana.title("Par más cercano")

tk.Label(ventana, text="Punto").grid(row=0, column=0)
tk.Label(ventana, text="X").grid(row=0, column=1)
tk.Label(ventana, text="Y").grid(row=0, column=2)

entradas = []
for i in range(5):
    tk.Label(ventana, text=f"P{i+1}").grid(row=i+1, column=0)
    x_entry = tk.Entry(ventana, width=5)
    y_entry = tk.Entry(ventana, width=5)
    x_entry.grid(row=i+1, column=1)
    y_entry.grid(row=i+1, column=2)
    entradas.append((x_entry, y_entry))

tk.Button(ventana, text="Llenar", command=llenar).grid(row=6, column=0, pady=10)
tk.Button(ventana, text="Limpiar", command=limpiar).grid(row=6, column=1)
tk.Button(ventana, text="Calcular", command=calcular).grid(row=6, column=2)

resultado = tk.Label(ventana, text="", fg="blue", font=("Arial", 10))
resultado.grid(row=7, column=0, columnspan=3)

ventana.mainloop()