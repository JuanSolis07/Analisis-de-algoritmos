import tkinter as tk

def saludar():
    nombre = entrada.get().strip()
    if not nombre:
        nombre = "mundo"
    lbl.config(text=f"Hola Compa, {nombre} mucho gusto")

root = tk.Tk()
root.title("Saludador de Compas")
root.geometry("360x220")
root.configure(background="lightblue")
lbl = tk.Label(root, text="Hola amiguito!, escribe tu nombre y presiona el botón, porfa",font=("Arial"))
lbl.pack(pady=20)

entrada = tk.Entry(root)
entrada.pack(pady=5)

btn = tk.Button(root, text="Saludar", command=saludar)
btn.pack(pady=20)

root.mainloop()