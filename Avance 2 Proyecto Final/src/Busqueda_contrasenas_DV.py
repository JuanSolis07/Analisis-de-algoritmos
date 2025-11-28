import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import time
import itertools
import string
import concurrent.futures
import multiprocessing
import heapq
from collections import Counter
import matplotlib.pyplot as plt
import csv

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

# -------------------------
# Huffman-like costs (para búsqueda voraz)
# -------------------------

def build_huffman_costs_from_freqs(freqs):
    """
    Dado un dict char->freq construye longitudes tipo Huffman (enteros)
    retornando char->length. Implementación que mantiene conjuntos en nodos.
    """
    # fallback
    if not freqs:
        return {}
    heap = [(f, {ch}) for ch, f in freqs.items()]
    heapq.heapify(heap)
    lengths = {ch: 0 for ch in freqs}
    if len(heap) == 1:
        ch = next(iter(freqs))
        lengths[ch] = 1
        return lengths
    while len(heap) > 1:
        f1, s1 = heapq.heappop(heap)
        f2, s2 = heapq.heappop(heap)
        for ch in s1:
            lengths[ch] += 1
        for ch in s2:
            lengths[ch] += 1
        heapq.heappush(heap, (f1 + f2, s1.union(s2)))
    return lengths


def build_costs_from_dictionary(wordlist, alphabet):
    """
    Construye un coste (int) por caracter a partir de un wordlist.
    Para caracteres no vistos asigna un coste mayor.
    """
    cnt = Counter()
    for w in wordlist:
        cnt.update(w)
    # asegurar que cada símbolo del alfabeto aparezca al menos con peso 1
    for ch in alphabet:
        cnt.setdefault(ch, 1)
    lengths = build_huffman_costs_from_freqs(cnt)
    max_len = max(lengths.values()) if lengths else len(alphabet)
    costs = {ch: lengths.get(ch, max_len + 2) for ch in alphabet}
    return costs

# -------------------------
# Worker: Divide y vencerás + versión voraz
# -------------------------
class DivideWorker:
    def __init__(self, gui_log):
        self._stop_event = threading.Event()
        self.gui_log = gui_log
        self._found_lock = threading.Lock()
        self._found = {}  # target -> (candidate, attempts, elapsed)

    def stop(self):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()

    # Diccionario (multi-target)
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
            if w in targets_set:
                elapsed = time.time() - start
                with self._found_lock:
                    if w not in self._found:
                        self._found[w] = (w, attempts, elapsed)
                        self.gui_log(f"[Dic]Encontrada en diccionario: '{w}' — intentos={attempts} — tiempo={format_seconds(elapsed)}")
            if attempts % 50 == 0:
                self.gui_log(f"[Dic] intentos={attempts} — última='{w}'")
        elapsed = time.time() - start
        self.gui_log(f"[Dic] Diccionario terminado — intentos={attempts} — tiempo={format_seconds(elapsed)}")
        return self._found

    # versión lexicográfica por partición (antigua)
    def _chunk_worker_lex(self, targets_set, charset, max_len, prefix, start_time, time_budget, attempts_counter, attempts_cap):
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
                    self.gui_log(f"[Divide] intentos={attempts:,} — rate≈{rate:.0f} it/s — última='{candidate}'")
                if candidate in targets_set:
                    elapsed = time.time() - start_time
                    with self._found_lock:
                        if candidate not in self._found:
                            self._found[candidate] = (candidate, attempts, elapsed)
                            self.gui_log(f"[Divide]¡Encontrada! '{candidate}' — intentos={attempts:,} — tiempo={format_seconds(elapsed)}")
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
                    self.gui_log(f"[Divide] intentos={attempts:,} — rate≈{rate:.0f} it/s — última='{candidate}'")
                if candidate in targets_set:
                    elapsed = time.time() - start_time
                    with self._found_lock:
                        if candidate not in self._found:
                            self._found[candidate] = (candidate, attempts, elapsed)
                            self.gui_log(f"[Divide] ✅ ¡Encontrada! '{candidate}' — intentos={attempts:,} — tiempo={format_seconds(elapsed)}")
                if attempts >= attempts_cap:
                    self.gui_log(f"[!] Tope de intentos alcanzado ({attempts:,}).")
                    self.stop()
                    return

    # versión voraz por partición (best-first usando heap)
    def _chunk_worker_priority(self, targets_set, charset, max_len, prefix, start_time, time_budget, attempts_counter, attempts_cap, char_costs, max_heap_size=200_000):
        if len(prefix) > max_len:
            return
        def prefix_cost(s):
            return sum(char_costs.get(ch, max(char_costs.values())+1) for ch in s)
        heap = []
        start_cost = prefix_cost(prefix)
        heapq.heappush(heap, (start_cost, prefix))
        while heap:
            if self.is_stopped():
                return
            if time_budget is not None and (time.time() - start_time) >= time_budget:
                return
            priority, candidate = heapq.heappop(heap)
            with attempts_counter.get_lock():
                attempts_counter.value += 1
                attempts = attempts_counter.value
            if attempts % 10000 == 0:
                elapsed = time.time() - start_time
                rate = attempts / elapsed if elapsed > 0 else 0
                self.gui_log(f"[Divide] intentos={attempts:,} — rate≈{rate:.0f} it/s — última='{candidate}'")
            if candidate in targets_set:
                elapsed = time.time() - start_time
                with self._found_lock:
                    if candidate not in self._found:
                        self._found[candidate] = (candidate, attempts, elapsed)
                        self.gui_log(f"[Divide] ✅ ¡Encontrada! '{candidate}' — intentos={attempts:,} — tiempo={format_seconds(elapsed)}")
            if attempts >= attempts_cap:
                self.gui_log(f"[!] Tope de intentos alcanzado ({attempts:,}).")
                self.stop()
                return
            if len(candidate) < max_len:
                for ch in charset:
                    if self.is_stopped():
                        return
                    new_cand = candidate + ch
                    new_priority = priority + char_costs.get(ch, 1000)
                    heapq.heappush(heap, (new_priority, new_cand))
                # poda simple para controlar memoria
                if len(heap) > max_heap_size:
                    K = max_heap_size // 2
                    smallest = heapq.nsmallest(K, heap)
                    heap.clear()
                    for it in smallest:
                        heapq.heappush(heap, it)

    def divide_and_conquer(self, targets, charset, max_len, partition_len=1, time_budget=None, max_attempts_cap=5_000_000, max_workers=None, use_priority=False, char_costs=None):
        self._stop_event.clear()
        self._found = {}
        start = time.time()
        targets_set = set(targets)
        attempts_counter = multiprocessing.Value('L', 0)
        if partition_len <= 0:
            partition_len = 1
        prefixes = [''.join(p) for p in itertools.product(charset, repeat=partition_len)]
        total_partitions = len(prefixes)
        self.gui_log(f"[Divide] Particiones={total_partitions} (partition_len={partition_len}) — max_len={max_len} — charset_size={len(charset)}")
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
                if use_priority:
                    fut = ex.submit(self._chunk_worker_priority, targets_set, charset, max_len, pref, start, time_budget, attempts_counter, max_attempts_cap, char_costs)
                else:
                    fut = ex.submit(self._chunk_worker_lex, targets_set, charset, max_len, pref, start, time_budget, attempts_counter, max_attempts_cap)
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
                            self.gui_log("[Divide] Presupuesto de tiempo agotado.")
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
            self.gui_log(f"[Divide]No encontradas para: {remaining} — tiempo={format_seconds(elapsed)} — intentos={attempts_counter.value:,}")
        else:
            self.gui_log(f"[Divide]Todas las contraseñas encontradas — intentos={attempts_counter.value:,} — tiempo={format_seconds(elapsed)}")
        return self._found

# -------------------------
# Interfaz gráfica
# -------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Simulador: Diccionario + Divide y vencerás (Huffman)")
        self.geometry("980x760")
        self.resizable(False, False)
        self.worker = DivideWorker(self.append_log)
        self.thread_dict = None
        self.thread_div = None
        self._last_run_targets = []
        self._last_found_times = {}

        top = ttk.Frame(self)
        top.pack(fill='x', padx=8, pady=8)
        ttk.Label(top, text="Contraseñas objetivo (separadas por coma):").grid(row=0, column=0, sticky='w')
        self.entry_pw = ttk.Entry(top, width=70, show="*")
        self.entry_pw.grid(row=0, column=1, sticky='w', padx=6)
        self.show_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Mostrar", variable=self.show_var, command=self.toggle_show).grid(row=0, column=2, sticky='w')

        nb = ttk.Notebook(self)
        nb.pack(fill='both', expand=True, padx=8, pady=8)

        # Diccionario tab
        tab_dic = ttk.Frame(nb)
        nb.add(tab_dic, text="Diccionario")
        ttk.Label(tab_dic, text="Diccionario incorporado (pequeño):").pack(anchor='w', padx=8, pady=(6,0))
        self.txt_dict = scrolledtext.ScrolledText(tab_dic, width=90, height=10)
        self.txt_dict.pack(padx=8, pady=6)
        self.txt_dict.insert('1.0', "\n".join(SMALL_DICTIONARY))
        frame_dic_controls = ttk.Frame(tab_dic)
        frame_dic_controls.pack(fill='x', padx=8, pady=4)
        ttk.Button(frame_dic_controls, text="Cargar TXT", command=self.load_dictionary_file).grid(row=0, column=4, padx=6)

        ttk.Label(frame_dic_controls, text="Delay por intento (s):").grid(row=0, column=0, sticky='w')
        self.spin_delay = ttk.Spinbox(frame_dic_controls, from_=0.0, to=1.0, increment=0.01, width=8)
        self.spin_delay.set("0.0")
        self.spin_delay.grid(row=0, column=1, sticky='w', padx=6)
        ttk.Button(frame_dic_controls, text="Iniciar (diccionario)", command=self.start_dictionary).grid(row=0, column=2, padx=6)
        ttk.Button(frame_dic_controls, text="Detener", command=self.stop).grid(row=0, column=3, padx=6)

        # Divide tab
        tab_div = ttk.Frame(nb)
        nb.add(tab_div, text="Divide y vencerás")
        frame_div = ttk.Frame(tab_div)
        frame_div.pack(fill='x', padx=8, pady=6)
        ttk.Label(frame_div, text="Charset (vacío -> a-z0-9):").grid(row=0, column=0, sticky='w')
        self.entry_charset = ttk.Entry(frame_div, width=40)
        self.entry_charset.grid(row=0, column=1, sticky='w', padx=6)
        ttk.Label(frame_div, text="Longitud máxima: ").grid(row=1, column=0, sticky='w', pady=(6,0))
        self.spin_maxlen = ttk.Spinbox(frame_div, from_=1, to=8, increment=1, width=6)
        self.spin_maxlen.set("4")
        self.spin_maxlen.grid(row=1, column=1, sticky='w', padx=6, pady=(6,0))
        ttk.Label(frame_div, text="Partition len (prefijo): ").grid(row=2, column=0, sticky='w', pady=(6,0))
        self.spin_partlen = ttk.Spinbox(frame_div, from_=1, to=3, increment=1, width=6)
        self.spin_partlen.set("1")
        self.spin_partlen.grid(row=2, column=1, sticky='w', padx=6, pady=(6,0))
        ttk.Label(frame_div, text="Presupuesto tiempo (s, vacío=ilimitado):").grid(row=3, column=0, sticky='w', pady=(6,0))
        self.entry_timebudget = ttk.Entry(frame_div, width=12)
        self.entry_timebudget.grid(row=3, column=1, sticky='w', padx=6, pady=(6,0))
        ttk.Label(frame_div, text="Tope de intentos (seguridad):").grid(row=4, column=0, sticky='w', pady=(6,0))
        self.spin_cap = ttk.Spinbox(frame_div, from_=1000, to=200_000_000, increment=1000, width=12)
        self.spin_cap.set("2000000")
        self.spin_cap.grid(row=4, column=1, sticky='w', padx=6, pady=(6,0))
        ttk.Label(frame_div, text="Hilos max (0=auto CPU):").grid(row=5, column=0, sticky='w', pady=(6,0))
        self.spin_workers = ttk.Spinbox(frame_div, from_=0, to=64, increment=1, width=8)
        self.spin_workers.set("0")
        self.spin_workers.grid(row=5, column=1, sticky='w', padx=6, pady=(6,0))
        self.priority_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_div, text="Usar búsqueda voraz (Huffman)", variable=self.priority_var).grid(row=6, column=0, columnspan=2, sticky='w', pady=(6,0))
        div_buttons = ttk.Frame(tab_div)
        div_buttons.pack(fill='x', padx=8, pady=8)
        ttk.Button(div_buttons, text="Iniciar ambos (diccionario + divide)", command=self.start_both).pack(side='left', padx=6)
        ttk.Button(div_buttons, text="Detener", command=self.stop).pack(side='left')
        ttk.Button(div_buttons, text="Mostrar gráfica", command=self.show_graph).pack(side='left', padx=6)
        ttk.Button(div_buttons, text="Exportar CSV", command=self.export_csv).pack(side='left', padx=6)

        ttk.Label(self, text="Registro:").pack(anchor='w', padx=8)
        self.logbox = scrolledtext.ScrolledText(self, height=18, state='disabled', wrap='word')
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
        if self.thread_dict and self.thread_dict.is_alive():
            messagebox.showinfo("Info", "Ya hay una operación de diccionario en curso. Deténla primero.")
            return
        self.append_log("[UI] Iniciando ataque por diccionario (multi-target)...")
        self.thread_dict = threading.Thread(target=self._run_dictionary, args=(targets, wl, delay), daemon=True)
        self.thread_dict.start()

    def load_dictionary_file(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de diccionario",
            filetypes=[("Archivo de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Limpiar y colocar el contenido en el cuadro del diccionario
            self.txt_dict.delete('1.0', 'end')
            self.txt_dict.insert('1.0', content)

            self.append_log(f"[UI] Diccionario cargado desde: {path}")

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el diccionario:\n{e}")

    def _run_dictionary(self, targets, wl, delay):
        res = self.worker.dictionary_attack_multi(targets, wl, delay=delay)
        if res:
            for k, v in res.items():
                _, _, elapsed = v
                self._last_found_times[k] = elapsed
        self._last_run_targets = targets
        self.append_log("[UI] Terminó la comprobación por diccionario.")

    def start_divide(self):
        raw = self.entry_pw.get().strip()
        if raw == "":
            messagebox.showinfo("Info", "Introduce al menos una contraseña objetivo (separadas por coma).")
            return
        targets = [t.strip() for t in raw.split(',') if t.strip()]
        self._last_run_targets = targets
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
        if self.thread_div and self.thread_div.is_alive():
            messagebox.showinfo("Info", "Ya hay una operación divide en curso. Deténla primero.")
            return
        workers_param = None if workers == 0 else workers
        self._last_found_times = {}
        use_priority = bool(self.priority_var.get())
        # construir char_costs usando diccionario actual + incluido
        wl = [w.strip() for w in self.txt_dict.get('1.0', 'end').splitlines() if w.strip()]
        merged_wl = wl + SMALL_DICTIONARY
        char_costs = build_costs_from_dictionary(merged_wl, charset)
        self.append_log(f"[UI] Iniciando divide y vencerás — objetivos={targets} — charset_size={len(charset)} — maxlen={maxlen} — partition_len={partlen} — time_budget={time_budget} — priority={use_priority}")
        self.thread_div = threading.Thread(target=self._run_divide, args=(targets, charset, maxlen, partlen, time_budget, cap, workers_param, use_priority, char_costs), daemon=True)
        self.thread_div.start()

    def _run_divide(self, targets, charset, maxlen, partlen, time_budget, cap, workers_param, use_priority, char_costs):
        res = self.worker.divide_and_conquer(targets, charset, maxlen, partition_len=partlen, time_budget=time_budget, max_attempts_cap=cap, max_workers=workers_param, use_priority=use_priority, char_costs=char_costs)
        if res:
            for k, v in res.items():
                _, _, elapsed = v
                self._last_found_times[k] = elapsed
        self.append_log("[UI] Terminó divide y vencerás.")

    def start_both(self):
        # lanza diccionario y divide al mismo tiempo
        raw = self.entry_pw.get().strip()
        if raw == "":
            messagebox.showinfo("Info", "Introduce al menos una contraseña objetivo (separadas por coma).")
            return
        targets = [t.strip() for t in raw.split(',') if t.strip()]
        # iniciar diccionario
        wl = [w.strip() for w in self.txt_dict.get('1.0', 'end').splitlines() if w.strip()]
        delay = float(self.spin_delay.get())
        if not self.thread_dict or not self.thread_dict.is_alive():
            self.thread_dict = threading.Thread(target=self._run_dictionary, args=(targets, wl, delay), daemon=True)
            self.thread_dict.start()
        # iniciar divide
        self.start_divide()

    def show_graph(self):
        if not self._last_run_targets:
            messagebox.showinfo("Info", "No hay ejecución reciente para graficar. Ejecuta una búsqueda primero.")
            return
        times = []
        for t in self._last_run_targets:
            times.append(self._last_found_times.get(t, float('nan')))
        cumulative = []
        max_so_far = 0.0
        for val in times:
            if val != val:
                cumulative.append(float('nan'))
            else:
                max_so_far = max(max_so_far, val)
                cumulative.append(max_so_far)
        x = list(range(1, len(times) + 1))
        plt.figure(figsize=(9, 5))
        plt.plot(x, cumulative, marker='o', label='Tiempo acumulado (max entre primeros k)')
        plt.bar(x, [v if v == v else 0 for v in times], alpha=0.4, label='Tiempo individual por objetivo')
        plt.xticks(x)
        plt.xlabel('Número de contraseñas (orden ingresado)')
        plt.ylabel('Tiempo (s)')
        plt.title('Comparativa: cantidad de contraseñas vs tiempo de descubrimiento')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def export_csv(self):
        if not self._last_run_targets:
            messagebox.showinfo("Info", "No hay datos para exportar.")
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv')])
        if not path:
            return
        rows = []
        for t in self._last_run_targets:
            rows.append((t, self._last_found_times.get(t, '')))
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['target','time_s'])
                writer.writerows(rows)
            messagebox.showinfo('OK', f'Datos exportados a {path}')
        except Exception as e:
            messagebox.showerror('Error', f'No se pudo escribir CSV: {e}')

    def stop(self):
        if (self.thread_div and self.thread_div.is_alive()) or (self.thread_dict and self.thread_dict.is_alive()):
            self.worker.stop()
            self.append_log("[*] Solicitud de detención enviada. Esperando a que termine...")
        else:
            self.append_log("[*] No hay operación en curso.")

if __name__ == "__main__":
    app = App()
    app.mainloop()