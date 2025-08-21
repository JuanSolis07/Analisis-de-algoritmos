import tkinter as tk
from tkinter import ttk, messagebox
import random
import time

# Implementación de los algoritmos de búsqueda
def busqueda_lineal(lista, x):
    for i in range(len(lista)):
        if lista[i] == x:
            return i
    return -1

def busqueda_binaria(lista, x):
    low = 0
    high = len(lista) - 1
    mid = 0

    while low <= high:
        mid = (high + low) // 2
        if lista[mid] < x:
            low = mid + 1
        elif lista[mid] > x:
            high = mid - 1
        else:
            return mid
    return -1

class GraficaTiempos(tk.Canvas):
    def __init__(self, parent, width=500, height=300):
        super().__init__(parent, width=width, height=height, bg="white")
        self.width = width
        self.height = height
        self.tiempos_lineal = {}
        self.tiempos_binaria = {}
        
    def actualizar_datos(self, tiempos_lineal, tiempos_binaria):
        self.tiempos_lineal = tiempos_lineal
        self.tiempos_binaria = tiempos_binaria
        self.dibujar_grafica()
        
    def dibujar_grafica(self):
        self.delete("all")
        
        if not self.tiempos_lineal or not self.tiempos_binaria:
            return
            
        # Configuración de la gráfica
        padding = 50
        max_y = max(max(self.tiempos_lineal.values()), max(self.tiempos_binaria.values())) * 1.1
        tamanos = sorted(self.tiempos_lineal.keys())
        num_barras = len(tamanos)
        bar_width = (self.width - 2 * padding) / (num_barras * 2 + 1)
        
        # Dibujar ejes
        self.create_line(padding, self.height - padding, self.width - padding, self.height - padding, width=2)  # Eje X
        self.create_line(padding, padding, padding, self.height - padding, width=2)  # Eje Y
        
        # Dibujar título y etiquetas
        self.create_text(self.width // 2, 20, text="Comparación de Tiempos de Búsqueda", font=("Arial", 12, "bold"))
        self.create_text(self.width // 2, self.height - 10, text="Tamaño de la Lista", font=("Arial", 10))
        self.create_text(15, self.height // 2, text="Tiempo (ms)", angle=90, font=("Arial", 10))
        
        # Dibujar barras para cada tamaño
        for i, tamano in enumerate(tamanos):
            x_pos = padding + (i * 2 + 1) * bar_width
            
            # Barra para búsqueda lineal
            bar_height_lineal = (self.tiempos_lineal[tamano] / max_y) * (self.height - 2 * padding)
            self.create_rectangle(
                x_pos - bar_width/2, self.height - padding - bar_height_lineal,
                x_pos, self.height - padding,
                fill="lightblue", outline="black"
            )
            self.create_text(x_pos - bar_width/4, self.height - padding - bar_height_lineal - 10, 
                            text=f"{self.tiempos_lineal[tamano]:.4f}", font=("Arial", 7))
            
            # Barra para búsqueda binaria
            bar_height_binaria = (self.tiempos_binaria[tamano] / max_y) * (self.height - 2 * padding)
            self.create_rectangle(
                x_pos, self.height - padding - bar_height_binaria,
                x_pos + bar_width/2, self.height - padding,
                fill="lightgreen", outline="black"
            )
            self.create_text(x_pos + bar_width/4, self.height - padding - bar_height_binaria - 10, 
                            text=f"{self.tiempos_binaria[tamano]:.4f}", font=("Arial", 7))
            
            # Etiqueta del tamaño
            self.create_text(x_pos, self.height - padding + 15, text=str(tamano), font=("Arial", 8))
        
        # Leyenda
        self.create_rectangle(self.width - 150, 40, self.width - 130, 50, fill="lightblue", outline="black")
        self.create_text(self.width - 120, 45, text="Búsqueda Lineal", anchor="w", font=("Arial", 9))
        
        self.create_rectangle(self.width - 150, 60, self.width - 130, 70, fill="lightgreen", outline="black")
        self.create_text(self.width - 120, 65, text="Búsqueda Binaria", anchor="w", font=("Arial", 9))

class SearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comparador de Algoritmos de Búsqueda")
        self.root.geometry("900x700")
        
        # Variables de instancia
        self.lista = []
        self.tiempos_lineal = {}
        self.tiempos_binaria = {}
        
        self.crear_interfaz()
        
    def crear_interfaz(self):
        # Marco principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configuración de expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # Sección de generación de datos
        ttk.Label(main_frame, text="Generación de datos", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        ttk.Label(main_frame, text="Tamaño de la lista:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.tamano_var = tk.StringVar(value="100")
        tamano_combo = ttk.Combobox(main_frame, textvariable=self.tamano_var, 
                                   values=["100", "1000", "10000", "100000"], state="readonly")
        tamano_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.generar_btn = ttk.Button(main_frame, text="Generar datos", command=self.generar_datos)
        self.generar_btn.grid(row=1, column=2, pady=5, padx=5)
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Sección de búsqueda
        ttk.Label(main_frame, text="Búsqueda de elemento", font=('Arial', 12, 'bold')).grid(row=3, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        ttk.Label(main_frame, text="Valor a buscar:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.valor_var = tk.StringVar()
        valor_entry = ttk.Entry(main_frame, textvariable=self.valor_var)
        valor_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        
        self.buscar_lineal_btn = ttk.Button(main_frame, text="Búsqueda Lineal", 
                                           command=lambda: self.realizar_busqueda('lineal'), state=tk.DISABLED)
        self.buscar_lineal_btn.grid(row=4, column=2, pady=5, padx=5)
        
        self.buscar_binaria_btn = ttk.Button(main_frame, text="Búsqueda Binaria", 
                                            command=lambda: self.realizar_busqueda('binaria'), state=tk.DISABLED)
        self.buscar_binaria_btn.grid(row=4, column=3, pady=5, padx=5)
        
        # Resultados de búsqueda
        self.resultado_var = tk.StringVar(value="Resultados aparecerán aquí")
        resultado_label = ttk.Label(main_frame, textvariable=self.resultado_var, wraplength=500)
        resultado_label.grid(row=5, column=0, columnspan=4, pady=10, sticky=tk.W)
        
        # Separador
        ttk.Separator(main_frame, orient='horizontal').grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        # Sección de comparación gráfica
        ttk.Label(main_frame, text="Comparación de tiempos de ejecución", font=('Arial', 12, 'bold')).grid(row=7, column=0, columnspan=2, pady=10, sticky=tk.W)
        
        self.comparar_btn = ttk.Button(main_frame, text="Generar Comparación", command=self.generar_comparacion)
        self.comparar_btn.grid(row=7, column=2, columnspan=2, pady=5)
        
        # Gráfica de tiempos
        self.grafica = GraficaTiempos(main_frame, width=800, height=300)
        self.grafica.grid(row=8, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Configurar expansión para la gráfica
        main_frame.rowconfigure(8, weight=1)
        
    def generar_datos(self):
        try:
            tamano = int(self.tamano_var.get())
            if tamano <= 0:
                messagebox.showerror("Error", "El tamaño debe ser un número positivo")
                return
                
            # Generar lista ordenada de enteros aleatorios
            self.lista = sorted([random.randint(0, tamano*10) for _ in range(tamano)])
            
            messagebox.showinfo("Éxito", f"Lista de {tamano} elementos generada y ordenada correctamente")
            
            # Habilitar botones de búsqueda
            self.buscar_lineal_btn.config(state=tk.NORMAL)
            self.buscar_binaria_btn.config(state=tk.NORMAL)
            
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese un tamaño válido")
    
    def realizar_busqueda(self, tipo):
        if not self.lista:
            messagebox.showerror("Error", "Primero debe generar datos")
            return
            
        try:
            valor = int(self.valor_var.get())
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese un valor numérico válido")
            return
            
        # Realizar la búsqueda y medir el tiempo
        inicio = time.perf_counter()
        
        if tipo == 'lineal':
            resultado = busqueda_lineal(self.lista, valor)
        else:
            resultado = busqueda_binaria(self.lista, valor)
            
        fin = time.perf_counter()
        tiempo_ms = (fin - inicio) * 1000  # Convertir a milisegundos
        
        # Mostrar resultados
        if resultado != -1:
            mensaje = f"Elemento encontrado en el índice {resultado} | "
        else:
            mensaje = "Elemento no encontrado | "
            
        mensaje += f"Tiempo de ejecución: {tiempo_ms:.6f} ms | Tamaño de lista: {len(self.lista)}"
        self.resultado_var.set(mensaje)
    
    def generar_comparacion(self):
        tamanos = [100, 1000, 10000, 100000]
        self.tiempos_lineal = {}
        self.tiempos_binaria = {}
        
        # Realizar mediciones para cada tamaño
        for tamano in tamanos:
            # Generar lista para este tamaño
            lista_temp = sorted([random.randint(0, tamano*10) for _ in range(tamano)])
            valor = random.choice(lista_temp)  # Asegurar que el valor existe en la lista
            
            # Medir tiempo para búsqueda lineal (promedio de 5 ejecuciones)
            tiempos_lineal = []
            for _ in range(5):
                inicio = time.perf_counter()
                busqueda_lineal(lista_temp, valor)
                fin = time.perf_counter()
                tiempos_lineal.append((fin - inicio) * 1000)
            self.tiempos_lineal[tamano] = sum(tiempos_lineal) / len(tiempos_lineal)
            
            # Medir tiempo para búsqueda binaria (promedio de 5 ejecuciones)
            tiempos_binaria = []
            for _ in range(5):
                inicio = time.perf_counter()
                busqueda_binaria(lista_temp, valor)
                fin = time.perf_counter()
                tiempos_binaria.append((fin - inicio) * 1000)
            self.tiempos_binaria[tamano] = sum(tiempos_binaria) / len(tiempos_binaria)
        
        # Actualizar gráfica
        self.grafica.actualizar_datos(self.tiempos_lineal, self.tiempos_binaria)

if __name__ == "__main__":
    root = tk.Tk()
    app = SearchApp(root)
    root.mainloop()