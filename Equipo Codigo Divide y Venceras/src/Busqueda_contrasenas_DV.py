import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import itertools
import string
import concurrent.futures
import multiprocessing
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

SMALL_DICTIONARY = [
    "password", "123456", "qwerty", "admin", "letmein",
    "secret", "welcome", "abc123", "monkey", "dragon"
]

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

#Worker de busqueda
class BruteWorker:
    def __init__(self, gui_log):
        self._stop_event = threading.Event()
        self.gui_log = gui_log
        self._found_lock = threading.Lock()
        self._found = {}  

    def stop(self):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()

    def dictionary_attack_multi(self, targets, wordlist, delay=0.0):
        self._stop_event.clear()
        start = time.time()
        attempts = 0
        targets_set = set(targets)
        for w in wordlist:
            if self.is_stopped():
                self.gui_log("[*] Detenido por usuario (diccionario).")
                return self._found
            attempts += 1
            if delay > 0:
                time.sleep(delay)
            if w in targets_set and w not in self._found:
                elapsed = time.time() - start
                self.gui_log(f"Encontrada en diccionario: '{w}' — intentos={attempts} — tiempo={format_seconds(elapsed)}")
                with self._found_lock:
                    self._found[w] = (w, attempts, elapsed)
            if attempts % 50 == 0:
                self.gui_log(f"[Dic] intentos={attempts} — última='{w}'")
        elapsed = time.time() - start
        self.gui_log(f"!!!Diccionario terminado — intentos={attempts} — tiempo={format_seconds(elapsed)}")
        return self._found

    def _chunk_worker(self, targets_set, charset, max_len, prefix, start_time, time_budget, attempts_counter, attempts_cap):
        if len(prefix) > max_len:
            return
        for L in range(len(prefix), max_len + 1):
            if self.is_stopped():
                return
            if time_budget is not None and (time.time() - start_time) >= time_budget:
                return
            if L == len(prefix):
                candidate = prefix
                with attempts_counter.get_lock():
                    attempts_counter.value += 1
                    attempts = attempts_counter.value
                if attempts % 10000 == 0:
                    elapsed = time.time() - start_time
                    rate = attempts / elapsed if elapsed > 0 else 0
                    self.gui_log(f"[Brute] intentos={attempts:,} — rate≈{rate:.0f} it/s — última='{candidate}'")
                if candidate in targets_set:
                    elapsed = time.time() - start_time
                    with self._found_lock:
                        if candidate not in self._found:
                            self._found[candidate] = (candidate, attempts, elapsed)
                            self.gui_log(f":) ¡Encontrada! '{candidate}' — intentos={attempts:,} — tiempo={format_seconds(elapsed)}")
                if attempts >= attempts_cap:
                    self.gui_log(f"[!] Tope de intentos alcanzado ({attempts:,}).")
                    self.stop()
                    return
                continue
            rem = L - len(prefix)
            for suf in itertools.product(charset, repeat=rem):
                if self.is_stopped():
                    return
                if time_budget is not None and (time.time() - start_time) >= time_budget:
                    return
                candidate = prefix + ''.join(suf)
                with attempts_counter.get_lock():
                    attempts_counter.value += 1
                    attempts = attempts_counter.value
                if attempts % 10000 == 0:
                    elapsed = time.time() - start_time
                    rate = attempts / elapsed if elapsed > 0 else 0
                    self.gui_log(f"[Brute] intentos={attempts:,} — rate≈{rate:.0f} it/s — última='{candidate}'")
                if candidate in targets_set:
                    elapsed = time.time() - start_time
                    with self._found_lock:
                        if candidate not in self._found:
                            self._found[candidate] = (candidate, attempts, elapsed)
                            self.gui_log(f":) ¡Encontrada! '{candidate}' — intentos={attempts:,} — tiempo={format_seconds(elapsed)}")
                if attempts >= attempts_cap:
                    self.gui_log(f"[!] Tope de intentos alcanzado ({attempts:,}).")
                    self.stop()
                    return

    def brute_force_divide_and_conquer(self, targets, charset, max_len, partition_len=1, time_budget=None, max_attempts_cap=5_000_000, max_workers=None):
        self._stop_event.clear()
        self._found = {}
        start = time.time()
        targets_set = set(targets)

        attempts_counter = multiprocessing.Value('L', 0)

        if partition_len <= 0:
            partition_len = 1
        prefixes = [''.join(p) for p in itertools.product(charset, repeat=partition_len)]

        total_partitions = len(prefixes)
        self.gui_log(f"[Brute-Divide] Particiones={total_partitions} (partition_len={partition_len}) — max_len={max_len} — charset_size={len(charset)}")

        if max_workers is None:
            max_workers = min(total_partitions, max(1, (multiprocessing.cpu_count() or 1)))
        max_workers = max(1, max_workers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = []
            for pref in prefixes:
                if self.is_stopped():
                    break
                if len(pref) > max_len:
                    continue
                fut = ex.submit(self._chunk_worker, targets_set, charset, max_len, pref, start, time_budget, attempts_counter, max_attempts_cap)
                futures.append(fut)
            try:
                if time_budget is None:
                    for fut in concurrent.futures.as_completed(futures):
                        if self.is_stopped():
                            break
                else:
                    end_time = start + time_budget
                    for fut in futures:
                        if self.is_stopped():
                            break
                        now = time.time()
                        if now >= end_time:
                            self.gui_log("[Brute-Divide] Presupuesto de tiempo agotado.")
                            self.stop()
                            break
                        try:
                            fut.result(timeout=max(0.1, end_time - now))
                        except concurrent.futures.TimeoutError:
                            continue
            except KeyboardInterrupt:
                self.stop()

        elapsed = time.time() - start
        remaining = [t for t in targets if t not in self._found]
        if remaining:
            self.gui_log(f"No encontradas para: {remaining} — tiempo={format_seconds(elapsed)} — intentos={attempts_counter.value:,}")
        else:
            self.gui_log(f"Todas las contraseñas encontradas — intentos={attempts_counter.value:,} — tiempo={format_seconds(elapsed)}")

        return self._found

#GUI del programa
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador educativo: Diccionario + Fuerza bruta (Divide y vencerás)")
        self.geometry("920x700")
        self.resizable(True, True)

        self.worker = BruteWorker(self.append_log)
        self.thread = None

        top = ttk.Frame(self)
        top.pack(fill='x', padx=8, pady=8)

        ttk.Label(top, text="Contraseñas objetivo (separadas por coma):").grid(row=0, column=0, sticky='w')
        self.entry_pw = ttk.Entry(top, width=60, show="*")
        self.entry_pw.grid(row=0, column=1, sticky='w', padx=6)
        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Mostrar", variable=self.show_var, command=self.toggle_show).grid(row=0, column=2, sticky='w')

        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=8, pady=8)

        tab_dic = ttk.Frame(nb)
        nb.add(tab_dic, text="Diccionario")

        ttk.Label(tab_dic, text="Diccionario incorporado (pequeño):").pack(anchor='w', padx=8, pady=(6,0))
        self.txt_dict = scrolledtext.ScrolledText(tab_dic, width=70, height=10)
        self.txt_dict.pack(padx=8, pady=6)
        self.txt_dict.insert('1.0', "\n".join(SMALL_DICTIONARY))

        frame_dic_controls = ttk.Frame(tab_dic)
        frame_dic_controls.pack(fill='x', padx=8, pady=4)
        ttk.Label(frame_dic_controls, text="Delay por intento (s):").grid(row=0, column=0, sticky='w')
        self.spin_delay = ttk.Spinbox(frame_dic_controls, from_=0.0, to=1.0, increment=0.01, width=8)
        self.spin_delay.set("0.0")
        self.spin_delay.grid(row=0, column=1, sticky='w', padx=6)

        ttk.Button(frame_dic_controls, text="Iniciar (diccionario para todos)", command=self.start_dictionary).grid(row=0, column=2, padx=6)
        ttk.Button(frame_dic_controls, text="Detener", command=self.stop).grid(row=0, column=3, padx=6)

        tab_br = ttk.Frame(nb)
        nb.add(tab_br, text="Fuerza bruta (divide y vencerás)")

        frame_br = ttk.Frame(tab_br)
        frame_br.pack(fill='x', padx=8, pady=6)

        ttk.Label(frame_br, text="Charset (vacío -> a-z0-9):").grid(row=0, column=0, sticky='w')
        self.entry_charset = ttk.Entry(frame_br, width=40)
        self.entry_charset.grid(row=0, column=1, sticky='w', padx=6)

        ttk.Label(frame_br, text="Longitud máxima: ").grid(row=1, column=0, sticky='w', pady=(6,0))
        self.spin_maxlen = ttk.Spinbox(frame_br, from_=1, to=8, increment=1, width=6)
        self.spin_maxlen.set("4")
        self.spin_maxlen.grid(row=1, column=1, sticky='w', padx=6, pady=(6,0))

        ttk.Label(frame_br, text="Partition len (prefijo): ").grid(row=2, column=0, sticky='w', pady=(6,0))
        self.spin_partlen = ttk.Spinbox(frame_br, from_=1, to=3, increment=1, width=6)
        self.spin_partlen.set("1")
        self.spin_partlen.grid(row=2, column=1, sticky='w', padx=6, pady=(6,0))

        ttk.Label(frame_br, text="Presupuesto tiempo (s, vacío=ilimitado):").grid(row=3, column=0, sticky='w', pady=(6,0))
        self.entry_timebudget = ttk.Entry(frame_br, width=12)
        self.entry_timebudget.grid(row=3, column=1, sticky='w', padx=6, pady=(6,0))

        ttk.Label(frame_br, text="Tope de intentos (seguridad):").grid(row=4, column=0, sticky='w', pady=(6,0))
        self.spin_cap = ttk.Spinbox(frame_br, from_=1000, to=200_000_000, increment=1000, width=12)
        self.spin_cap.set("2000000")
        self.spin_cap.grid(row=4, column=1, sticky='w', padx=6, pady=(6,0))

        ttk.Label(frame_br, text="Hilos max (0=auto CPU):").grid(row=5, column=0, sticky='w', pady=(6,0))
        self.spin_workers = ttk.Spinbox(frame_br, from_=0, to=64, increment=1, width=8)
        self.spin_workers.set("0")
        self.spin_workers.grid(row=5, column=1, sticky='w', padx=6, pady=(6,0))

        br_buttons = ttk.Frame(tab_br)
        br_buttons.pack(fill='x', padx=8, pady=8)
        ttk.Button(br_buttons, text="Iniciar fuerza bruta (divide)", command=self.start_bruteforce).pack(side='left', padx=6)
        ttk.Button(br_buttons, text="Detener", command=self.stop).pack(side='left')
        ttk.Button(br_buttons, text="Benchmark: n vs tiempo", command=self.start_benchmark).pack(side='left', padx=6)

        ttk.Label(self, text="Registro:").pack(anchor='w', padx=8)
        self.logbox = scrolledtext.ScrolledText(self, height=12, state='disabled', wrap='word')
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
        raw = self.entry_pw.get().strip()
        if raw == "":
            messagebox.showinfo("Info", "Introduce al menos una contraseña objetivo (separadas por coma).")
            return
        targets = [t.strip() for t in raw.split(',') if t.strip()]
        wl = [w.strip() for w in self.txt_dict.get('1.0', 'end').splitlines() if w.strip()]
        if not wl:
            messagebox.showinfo("Info", "El diccionario está vacío.")
            return
        delay = float(self.spin_delay.get())
        if self.thread and self.thread.is_alive():
            messagebox.showinfo("Info", "Ya hay una operación en curso. Deténla primero.")
            return
        self.append_log("Iniciando ataque por diccionario (multi-target)...")
        self.thread = threading.Thread(target=self._run_dictionary, args=(targets, wl, delay), daemon=True)
        self.thread.start()

    def _run_dictionary(self, targets, wl, delay):
        res = self.worker.dictionary_attack_multi(targets, wl, delay=delay)
        if res:
            for k, v in res.items():
                pass
        self.append_log("Terminó la comprobación por diccionario.")

    def start_bruteforce(self):
        raw = self.entry_pw.get().strip()
        if raw == "":
            messagebox.showinfo("Info", "Introduce al menos una contraseña objetivo (separadas por coma).")
            return
        targets = [t.strip() for t in raw.split(',') if t.strip()]
        charset_input = self.entry_charset.get().strip()
        if charset_input:
            charset = list(dict.fromkeys(charset_input))
        else:
            charset = list(string.ascii_lowercase + string.digits)
        try:
            maxlen = int(self.spin_maxlen.get())
            cap = int(self.spin_cap.get())
            partlen = int(self.spin_partlen.get())
            workers = int(self.spin_workers.get())
        except ValueError:
            messagebox.showerror("Error", "Parámetros inválidos.")
            return
        tb_raw = self.entry_timebudget.get().strip()
        time_budget = None
        if tb_raw:
            try:
                time_budget = float(tb_raw)
                if time_budget <= 0:
                    time_budget = None
            except ValueError:
                messagebox.showerror("Error", "Presupuesto de tiempo inválido.")
                return
        est_total = sum(len(charset) ** L for L in range(1, maxlen + 1))
        if est_total > 20_000_000:
            if not messagebox.askyesno("Advertencia", f"El número estimado de combinaciones es {est_total:,}.\nEsto puede tardar mucho. ¿Deseas continuar?"):
                return
        if self.thread and self.thread.is_alive():
            messagebox.showinfo("Info", "Ya hay una operación en curso. Deténla primero.")
            return
        workers_param = None if workers == 0 else workers
        self.append_log(f"Iniciando fuerza bruta (divide y vencerás) — objetivos={targets} — charset_size={len(charset)} — maxlen={maxlen} — partition_len={partlen} — time_budget={time_budget}")
        self.thread = threading.Thread(target=self._run_brute, args=(targets, charset, maxlen, partlen, time_budget, cap, workers_param), daemon=True)
        self.thread.start()

    def _run_brute(self, targets, charset, maxlen, partlen, time_budget, cap, workers_param):
        res = self.worker.brute_force_divide_and_conquer(targets, charset, max_len=maxlen, partition_len=partlen, time_budget=time_budget, max_attempts_cap=cap, max_workers=workers_param)
        if res:
            for k, v in res.items():
                pass
        self.append_log("Terminó la fuerza bruta (divide y vencerás).")
#logica y funcionamiento de los campos de busqueda 
    def start_benchmark(self):
        charset_input = self.entry_charset.get().strip()
        if charset_input:
            charset = list(dict.fromkeys(charset_input))
        else:
            charset = list(string.ascii_lowercase + string.digits)
        try:
            maxlen = int(self.spin_maxlen.get())
            cap = int(self.spin_cap.get())
            partlen = int(self.spin_partlen.get())
            workers = int(self.spin_workers.get())
        except ValueError:
            messagebox.showerror("Error", "Parámetros inválidos.")
            return
        tb_raw = self.entry_timebudget.get().strip()
        time_budget = None
        if tb_raw:
            try:
                time_budget = float(tb_raw)
                if time_budget <= 0:
                    time_budget = None
            except ValueError:
                messagebox.showerror("Error", "Presupuesto de tiempo inválido.")
                return
        est_total = sum(len(charset) ** L for L in range(1, maxlen + 1))
        if est_total > 50_000_000:
            if not messagebox.askyesno("Advertencia", f"El número estimado de combinaciones es {est_total:,}.\n"
                                                     "El benchmark (peor caso) puede tardar mucho. ¿Deseas continuar?"):
                return
        if self.thread and self.thread.is_alive():
            messagebox.showinfo("Info", "Ya hay una operación en curso. Deténla primero.")
            return
        workers_param = None if workers == 0 else workers
        self.append_log(f"Iniciando benchmark n vs tiempo (divide y vencerás) — charset_size={len(charset)} — maxlen={maxlen} — partition_len={partlen}")
        self.thread = threading.Thread(target=self._run_benchmark, args=(charset, maxlen, partlen, time_budget, cap, workers_param), daemon=True)
        self.thread.start()

    def _run_benchmark(self, charset, maxlen, partlen, time_budget, cap, workers_param):
        lengths = []
        times = []
        for L in range(1, maxlen + 1):
            if self.worker.is_stopped():
                self.append_log("[*] Benchmark detenido por usuario.")
                break
            target = ''.join([charset[-1]] * L)
            self.append_log(f"[Benchmark] L={L}: probando objetivo='{target}' (peor caso)...")
            start = time.time()
            res = self.worker.brute_force_divide_and_conquer([target], charset, max_len=L, partition_len=partlen, time_budget=time_budget, max_attempts_cap=cap, max_workers=workers_param)
            elapsed = time.time() - start
            found = target in res
            lengths.append(L)
            times.append(elapsed)
            if found:
                candidate, attempts, worker_elapsed = res[target]
                self.append_log(f"[Benchmark] L={L}: encontrado en {attempts:,} intentos — tiempo={format_seconds(worker_elapsed)} (medido={format_seconds(elapsed)})")
            else:
                self.append_log(f"[Benchmark] L={L}: NO encontrado en el tiempo/intentOS permitidos — tiempo medido={format_seconds(elapsed)}")
            if self.worker.is_stopped():
                break
        if lengths:
            try:
                self._show_plot(lengths, times)
            except Exception as e:
                self.append_log(f"[!] Error al generar la gráfica: {e}")
        self.append_log("Benchmark finalizado.")

    def _show_plot(self, lengths, times):
        fig, ax = plt.subplots(figsize=(7,4))
        ax.plot(lengths, times, marker='o')
        ax.set_xlabel('Longitud (n)')
        ax.set_ylabel('Tiempo (s)')
        ax.set_title('Benchmark: longitud vs tiempo (peor caso) — Divide y vencerás')
        ax.grid(True)
        win = tk.Toplevel(self)
        win.title('Gráfica: n vs tiempo')
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.pack(fill='both', expand=True)

    def _run_brute(self, targets, charset, maxlen, partlen, time_budget, cap, workers_param):
        res = self.worker.brute_force_divide_and_conquer(targets, charset, max_len=maxlen, partition_len=partlen, time_budget=time_budget, max_attempts_cap=cap, max_workers=workers_param)
        if res:
            for k, v in res.items():
                pass
        self.append_log("Terminó divide y vencerás.")

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.worker.stop()
            self.append_log("[*] Solicitud de detención enviada. Esperando a que termine...")
        else:
            self.append_log("[*] No hay operación en curso.")

if __name__ == "__main__":
    app = App()
    app.mainloop()