# main.py
import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import Algoritmo_huffman
from Algoritmo_huffman import (
    guardar_comprimido_binario,
    leer_comprimido_binario,
    reconstruir_arbol_desde_codigos
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class HuffmanApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Compresor Huffman (con .nogpu real)")
        self.geometry("750x600")

        self.texto_original = ""
        self.codificado = ""
        self.raiz = None
        self.codigos = {}
        self.ruta_archivo = ""
        self.archivo_comprimido = ""

        # --- UI ---
        self.boton_cargar = ctk.CTkButton(self, text="📂 Cargar archivo", command=self.cargar_archivo)
        self.boton_cargar.pack(pady=10)

        self.boton_codificar = ctk.CTkButton(self, text="⚙️ Codificar y guardar .nogpu", command=self.codificar)
        self.boton_codificar.pack(pady=10)

        self.boton_decodificar = ctk.CTkButton(self, text="🔁 Decodificar desde .nogpu", command=self.decodificar)
        self.boton_decodificar.pack(pady=10)

        self.resultado = ctk.CTkTextbox(self, width=650, height=300)
        self.resultado.pack(pady=15)

        self.etiqueta_info = ctk.CTkLabel(self, text="")
        self.etiqueta_info.pack(pady=5)

    def cargar_archivo(self):
        ruta = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt")])
        if not ruta:
            return
        self.ruta_archivo = ruta
        with open(ruta, "r", encoding="utf-8") as f:
            self.texto_original = f.read()
        self.resultado.delete("1.0", "end")
        self.resultado.insert("end", f"Archivo cargado: {os.path.basename(ruta)}\n\n{self.texto_original}")
        self.etiqueta_info.configure(text=f"Tamaño original: {len(self.texto_original)} caracteres")

    def codificar(self):
        if not self.texto_original:
            messagebox.showwarning("Aviso", "Primero carga un archivo.")
            return

        frec = Algoritmo_huffman.calcular_frecuencias(self.texto_original)
        self.raiz = Algoritmo_huffman.construir_arbol(frec)
        self.codigos = Algoritmo_huffman.generar_codigos(self.raiz)
        self.codificado = Algoritmo_huffman.codificar_texto(self.texto_original, self.codigos)

        # Guardar el archivo comprimido en formato binario (.nogpu)
        nombre_salida = os.path.splitext(self.ruta_archivo)[0] + "_comprimido.nogpu"
        guardar_comprimido_binario(nombre_salida, self.codificado, self.codigos)
        self.archivo_comprimido = nombre_salida

        # Mostrar resultados y eficiencia
        eficiencia = Algoritmo_huffman.calcular_eficiencia(self.texto_original, self.codificado)

        self.resultado.delete("1.0", "end")
        self.resultado.insert("end", "=== Códigos Huffman ===\n")
        for c, code in self.codigos.items():
            if c == "\n":
                c_visible = "\\n"
            elif c == " ":
                c_visible = "(espacio)"
            else:
                c_visible = c
            self.resultado.insert("end", f"'{c_visible}': {code}\n")

        self.resultado.insert("end", f"\nArchivo comprimido guardado como: {os.path.basename(nombre_salida)}")
        original_size = os.path.getsize(self.ruta_archivo)
        compressed_size = os.path.getsize(nombre_salida)

        self.etiqueta_info.configure(
            text=f"Tamaño original: {original_size} bytes | Comprimido: {compressed_size} bytes\n"
                 f"Eficiencia teórica: {eficiencia:.2f}%"
        )

    def decodificar(self):
        if not self.archivo_comprimido or not os.path.exists(self.archivo_comprimido):
            messagebox.showwarning("Aviso", "Primero codifica (genera un archivo .nogpu).")
            return

        # Leer el archivo comprimido en binario y reconstruir árbol
        bits, cods = leer_comprimido_binario(self.archivo_comprimido)
        raiz = reconstruir_arbol_desde_codigos(cods)

        texto_decodificado = Algoritmo_huffman.decodificar_texto(bits, raiz)

        # Guardar el texto decodificado
        nombre_salida = os.path.splitext(self.ruta_archivo)[0] + "_decodificado.txt"
        with open(nombre_salida, "w", encoding="utf-8") as f:
            f.write(texto_decodificado)

        # Mostrar resultado
        self.resultado.delete("1.0", "end")
        self.resultado.insert("end", "=== Texto decodificado ===\n")
        self.resultado.insert("end", texto_decodificado)
        self.etiqueta_info.configure(
            text=f"Texto decodificado guardado como: {os.path.basename(nombre_salida)}"
        )


if __name__ == "__main__":
    app = HuffmanApp()
    app.mainloop()