import tkinter as tk

root = tk.Tk()
root.title("Mi primera GUI en Python")
root.geometry("500x600")

lbl = tk.Label(root, text="¡Hola, GUI!",fg="orange", bg="black")
root.configure(bg="yellow")
lbl.pack(pady=100)

root.mainloop()