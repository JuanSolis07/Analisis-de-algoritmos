import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import itertools
import string

# -------------------------
# Diccionario pequeño incluido
# -------------------------
SMALL_DICTIONARY = [
    "password", "123456", "qwerty", "admin", "letmein",
    "secret", "welcome", "abc123", "monkey", "dragon"
]

# -------------------------
# Utilidades
# -------------------------
def format_seconds(sec):
    if sec < 1:
        return f"{sec*1000:.0f} ms"
    if sec < 60:
        return f"{sec:.2f} s"
    m = sec / 60
    if m < 60:
        return f"{m:.2f} min"
    h = m / 60
    if h < 24:
        return f"{h:.2f} h"
    d = h / 24
    return f"{d:.2f} d"

# -------------------------
# Worker que hace la búsqueda
# -------------------------
class BruteWorker:
    def __init__(self, gui_log):
        self._stop = False
        self.gui_log = gui_log

    def stop(self):
        self._stop = True

    def dictionary_attack(self, target, wordlist, delay=0.0):
        """
        Prueba cada palabra del wordlist contra target.
        delay: segundos a dormir entre intentos (0.0 = ninguno)
        """
        self._stop = False
        start = time.time()
        attempts = 0
        for w in wordlist:
            if self._stop:
                self.gui_log("[*] Detenido por usuario.")
                return None
            attempts += 1
            if delay > 0:
                time.sleep(delay)
            if w == target:
                elapsed = time.time() - start
                self.gui_log(f"Encontrada en diccionario: '{w}' — intentos={attempts} — tiempo={format_seconds(elapsed)}")
                return w, attempts, elapsed
            # log periódico
            if attempts % 50 == 0:
                self.gui_log(f"[Dic] intentos={attempts} — última='{w}'")
        elapsed = time.time() - start
        self.gui_log(f"No encontrada en el diccionario (intentados={attempts}) — tiempo={format_seconds(elapsed)}")
        return None

    def brute_force(self, target, charset, max_len, max_attempts_cap=5_000_000):
        """
        Fuerza bruta real (genera combinaciones con itertools.product).
        Se recomienda usar charset pequeño y max_len pequeño para pruebas.
        max_attempts_cap: tope de intentos para evitar bloqueos accidentales.
        """
        self._stop = False
        start = time.time()
        attempts = 0
        # iterar por longitud creciente
        for L in range(1, max_len + 1):
            if self._stop:
                self.gui_log("[*] Detenido por usuario.")
                return None
            self.gui_log(f"[Brute] Probando longitud L={L} ...")
            # product genera en orden lexicográfico
            for tup in itertools.product(charset, repeat=L):
                if self._stop:
                    self.gui_log("[*] Detenido por usuario.")
                    return None
                attempts += 1
                candidate = ''.join(tup)
                if attempts % 10000 == 0:
                    # informe periódico
                    elapsed = time.time() - start
                    rate = attempts / elapsed if elapsed > 0 else 0
                    self.gui_log(f"[Brute] intentos={attempts:,} — rate≈{rate:.0f} it/s — última='{candidate}'")
                if candidate == target:
                    elapsed = time.time() - start
                    self.gui_log(f"¡Encontrada! '{candidate}' — intentos={attempts:,} — tiempo={format_seconds(elapsed)}")
                    return candidate, attempts, elapsed
                # seguridad: evitar explosión accidental
                if attempts >= max_attempts_cap:
                    elapsed = time.time() - start
                    self.gui_log(f"[!] Tope de intentos alcanzado ({attempts:,}). Interrumpiendo para evitar bloqueo. Tiempo={format_seconds(elapsed)}")
                    return None
        elapsed = time.time() - start
        self.gui_log(f"❌ No encontrada tras {attempts:,} intentos — tiempo={format_seconds(elapsed)}")
        return None

# -------------------------
# Interfaz gráfica simple
# -------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador educativo: Diccionario + Fuerza bruta")
        self.geometry("760x520")
        self.resizable(False, False)

        self.worker = BruteWorker(self.append_log)
        self.thread = None

        # Layout
        top = ttk.Frame(self)
        top.pack(fill='x', padx=8, pady=8)

        ttk.Label(top, text="Contraseña (prueba local):").grid(row=0, column=0, sticky='w')
        self.entry_pw = ttk.Entry(top, width=30, show="*")
        self.entry_pw.grid(row=0, column=1, sticky='w', padx=6)
        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Mostrar", variable=self.show_var, command=self.toggle_show).grid(row=0, column=2, sticky='w')

        # Tabs
        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=8, pady=8)

        # Diccionario tab
        tab_dic = ttk.Frame(nb)
        nb.add(tab_dic, text="Diccionario")

        ttk.Label(tab_dic, text="Diccionario incorporado (pequeño):").pack(anchor='w', padx=8, pady=(6,0))
        self.txt_dict = scrolledtext.ScrolledText(tab_dic, width=60, height=10)
        self.txt_dict.pack(padx=8, pady=6)
        # precargar el diccionario pequeño
        self.txt_dict.insert('1.0', "\n".join(SMALL_DICTIONARY))

        frame_dic_controls = ttk.Frame(tab_dic)
        frame_dic_controls.pack(fill='x', padx=8, pady=4)
        ttk.Label(frame_dic_controls, text="Delay por intento (s):").grid(row=0, column=0, sticky='w')
        self.spin_delay = ttk.Spinbox(frame_dic_controls, from_=0.0, to=1.0, increment=0.01, width=8)
        self.spin_delay.set("0.0")
        self.spin_delay.grid(row=0, column=1, sticky='w', padx=6)

        ttk.Button(frame_dic_controls, text="Iniciar (diccionario)", command=self.start_dictionary).grid(row=0, column=2, padx=6)
        ttk.Button(frame_dic_controls, text="Detener", command=self.stop).grid(row=0, column=3, padx=6)

        # Brute-force tab
        tab_br = ttk.Frame(nb)
        nb.add(tab_br, text="Fuerza bruta")

        frame_br = ttk.Frame(tab_br)
        frame_br.pack(fill='x', padx=8, pady=6)

        ttk.Label(frame_br, text="Charset (vacío -> a-z0-9):").grid(row=0, column=0, sticky='w')
        self.entry_charset = ttk.Entry(frame_br, width=30)
        self.entry_charset.grid(row=0, column=1, sticky='w', padx=6)

        ttk.Label(frame_br, text="Longitud máxima:").grid(row=1, column=0, sticky='w', pady=(6,0))
        self.spin_maxlen = ttk.Spinbox(frame_br, from_=1, to=6, increment=1, width=6)
        self.spin_maxlen.set("4")
        self.spin_maxlen.grid(row=1, column=1, sticky='w', padx=6, pady=(6,0))

        ttk.Label(frame_br, text="Tope de intentos (proteger):").grid(row=2, column=0, sticky='w', pady=(6,0))
        self.spin_cap = ttk.Spinbox(frame_br, from_=1000, to=50_000_000, increment=1000, width=12)
        self.spin_cap.set("2000000")
        self.spin_cap.grid(row=2, column=1, sticky='w', padx=6, pady=(6,0))

        br_buttons = ttk.Frame(tab_br)
        br_buttons.pack(fill='x', padx=8, pady=8)
        ttk.Button(br_buttons, text="Iniciar fuerza bruta", command=self.start_bruteforce).pack(side='left', padx=6)
        ttk.Button(br_buttons, text="Detener", command=self.stop).pack(side='left')

        # Log
        ttk.Label(self, text="Registro:").pack(anchor='w', padx=8)
        self.logbox = scrolledtext.ScrolledText(self, height=10, state='disabled', wrap='word')
        self.logbox.pack(fill='both', padx=8, pady=(0,8), expand=True)

    def toggle_show(self):
        self.entry_pw.config(show="" if self.show_var.get() else "*")

    def append_log(self, text):
        ts = time.strftime("%H:%M:%S")
        self.logbox.config(state='normal')
        self.logbox.insert('end', f"[{ts}] {text}\n")
        self.logbox.see('end')
        self.logbox.config(state='disabled')

    def start_dictionary(self):
        pw = self.entry_pw.get()
        if pw == "":
            messagebox.showinfo("Info", "Introduce la contraseña de prueba (local).")
            return
        # obtener wordlist del cuadro de texto
        wl = [w.strip() for w in self.txt_dict.get('1.0', 'end').splitlines() if w.strip()]
        if not wl:
            messagebox.showinfo("Info", "El diccionario está vacío.")
            return
        delay = float(self.spin_delay.get())
        # ejecutar en hilo
        if self.thread and self.thread.is_alive():
            messagebox.showinfo("Info", "Ya hay una operación en curso. Deténla primero.")
            return
        self.append_log("Iniciando ataque por diccionario (local)...")
        self.thread = threading.Thread(target=self._run_dictionary, args=(pw, wl, delay), daemon=True)
        self.thread.start()

    def _run_dictionary(self, pw, wl, delay):
        res = self.worker.dictionary_attack(pw, wl, delay=delay)
        if res is None:
            self.append_log("Terminó la comprobación por diccionario (no encontrada o detenido).")

    def start_bruteforce(self):
        pw = self.entry_pw.get()
        if pw == "":
            messagebox.showinfo("Info", "Introduce la contraseña de prueba (local).")
            return
        charset_input = self.entry_charset.get().strip()
        if charset_input:
            charset = list(dict.fromkeys(charset_input))  # chars únicos preservando orden
        else:
            # por defecto: a-z y 0-9
            charset = list(string.ascii_lowercase + string.digits)
        try:
            maxlen = int(self.spin_maxlen.get())
            cap = int(self.spin_cap.get())
        except ValueError:
            messagebox.showerror("Error", "Longitud máxima o tope inválido.")
            return
        # aviso sobre tamaño
        est_total = sum(len(charset) ** L for L in range(1, maxlen + 1))
        if est_total > 5_000_000:
            if not messagebox.askyesno("Advertencia", f"El número estimado de combinaciones es {est_total:,}.\n"
                                                     "Esto puede tardar mucho. ¿Deseas continuar?"):
                return
        if self.thread and self.thread.is_alive():
            messagebox.showinfo("Info", "Ya hay una operación en curso. Deténla primero.")
            return
        self.append_log(f"Iniciando fuerza bruta (charset size={len(charset)}, maxlen={maxlen}) ...")
        self.thread = threading.Thread(target=self._run_brute, args=(pw, charset, maxlen, cap), daemon=True)
        self.thread.start()

    def _run_brute(self, pw, charset, maxlen, cap):
        res = self.worker.brute_force(pw, charset, maxlen, max_attempts_cap=cap)
        if res is None:
            self.append_log("Terminó la fuerza bruta (no encontrada o detenido).")

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.worker.stop()
            self.append_log("[*] Solicitud de detención enviada. Esperando a que termine...")
        else:
            self.append_log("[*] No hay operación en curso.")

if __name__ == "__main__":
    app = App()
    app.mainloop()