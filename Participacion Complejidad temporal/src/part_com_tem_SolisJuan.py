import random
import time
import matplotlib.pyplot as plt

def Generador(N):
    """Genera una lista aleatoria de N enteros"""
    lista_base = list(range(1, N*5)) 
    return random.sample(lista_base, N)

def bubblesort(vector):
    n = len(vector)
    for i in range(n - 1):
        for j in range(0, n - i - 1):
            if vector[j] > vector[j + 1]:
                vector[j], vector[j + 1] = vector[j + 1], vector[j]
    return vector


def mergesort(vector):
    def merge(v):
        if len(v) > 1:
            medio = len(v) // 2
            izq = v[:medio]
            der = v[medio:]

            merge(izq)
            merge(der)

            i = j = k = 0
            while i < len(izq) and j < len(der):
                if izq[i] < der[j]:
                    v[k] = izq[i]
                    i += 1
                else:
                    v[k] = der[j]
                    j += 1
                k += 1

            while i < len(izq):
                v[k] = izq[i]
                i += 1
                k += 1

            while j < len(der):
                v[k] = der[j]
                j += 1
                k += 1
    merge(vector)
    return vector


def quicksort(vector):
    def quick(v, start, end):
        if start >= end:
            return

        def particion(v, start, end):
            pivot = v[start]
            menor = start + 1
            mayor = end

            while True:
                while menor <= mayor and v[mayor] >= pivot:
                    mayor -= 1
                while menor <= mayor and v[menor] <= pivot:
                    menor += 1
                if menor <= mayor:
                    v[menor], v[mayor] = v[mayor], v[menor]
                else:
                    break
            v[start], v[mayor] = v[mayor], v[start]
            return mayor

        p = particion(v, start, end)
        quick(v, start, p - 1)
        quick(v, p + 1, end)

    quick(vector, 0, len(vector) - 1)
    return vector

def Ordenador(lista, algoritmo):
    copia = lista.copy()
    inicio = time.time()

    if algoritmo == "Bubble":
        bubblesort(copia)
    elif algoritmo == "Merge":
        mergesort(copia)
    elif algoritmo == "Quick":
        quicksort(copia)

    fin = time.time()
    return fin - inicio

def Graficador(resultados):
    for algoritmo, tiempos in resultados.items():
        plt.plot(list(tiempos.keys()), list(tiempos.values()), label=algoritmo)

    plt.xlabel("Tamaño de la lista (N)")
    plt.ylabel("Tiempo de ejecución (segundos)")
    plt.title("Comparación de algoritmos de ordenamiento")
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    tamanos = range(50, 1001, 50) 
    algoritmos = ["Bubble", "Merge", "Quick"]

    resultados = {alg: {} for alg in algoritmos}

    for N in tamanos:
        lista = Generador(N)
        print(f"\nProbando con N = {N}")
        for alg in algoritmos:
            tiempo = Ordenador(lista, alg)
            resultados[alg][N] = tiempo
            print(f"{alg} sort tardó {tiempo:.6f} segundos")

    
    Graficador(resultados)


if __name__ == "__main__":
    main()