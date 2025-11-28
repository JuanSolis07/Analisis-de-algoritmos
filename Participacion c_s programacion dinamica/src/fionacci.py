import time
import matplotlib.pyplot as plt
from memory_profiler import memory_usage


def fib_bruto(n):
    if n <= 1:
        return n
    return fib_bruto(n - 1) + fib_bruto(n - 2)

def fib_dinamico(n):
    if n <= 1:
        return n
    fib = [0, 1]
    for i in range(2, n + 1):
        fib.append(fib[i - 1] + fib[i - 2])
    return fib[n]


def medir_tiempo(func, n):
    inicio = time.time()
    func(n)
    fin = time.time()
    return fin - inicio


def medir_memoria(func, n):
    uso = memory_usage((func, (n,)), max_iterations=1)
    return max(uso) - min(uso)


if __name__ == "__main__":
    ns = [5, 10, 20, 25, 30, 35]
    tiempos_bruto = []
    tiempos_dinamico = []
    memoria_bruto = []
    memoria_dinamico = []

    for n in ns:
        print(f"Calculando para n={n}...")

        
        t_b = medir_tiempo(fib_bruto, n)
        t_d = medir_tiempo(fib_dinamico, n)
        tiempos_bruto.append(t_b)
        tiempos_dinamico.append(t_d)

        
        m_b = medir_memoria(fib_bruto, n)
        m_d = medir_memoria(fib_dinamico, n)
        memoria_bruto.append(m_b)
        memoria_dinamico.append(m_d)


    plt.figure(figsize=(8, 5))
    plt.plot(ns, tiempos_bruto, marker='o', label="Fuerza bruta (recursiva)")
    plt.plot(ns, tiempos_dinamico, marker='o', label="Programación dinámica (iterativa)")
    plt.xlabel("n")
    plt.ylabel("Tiempo (segundos)")
    plt.title("Comparación temporal de Fibonacci")
    plt.legend()
    plt.grid(True)
    plt.show()

    
    plt.figure(figsize=(8, 5))
    plt.plot(ns, memoria_bruto, marker='o', label="Fuerza bruta (recursiva)")
    plt.plot(ns, memoria_dinamico, marker='o', label="Programación dinámica (iterativa)")
    plt.xlabel("n")
    plt.ylabel("Memoria usada (MiB)")
    plt.title("Comparación de uso de memoria de Fibonacci")
    plt.legend()
    plt.grid(True)
    plt.show()