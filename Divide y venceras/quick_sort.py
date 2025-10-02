def quick_sort(arr):
    if len(arr) <= 1:
        return arr  # Caso base: listas de 0 o 1 elementos ya están ordenadas

    pivot = arr[len(arr) // 2]  # Selecciona el pivote (aquí usamos el elemento central)

    left = [x for x in arr if x < pivot]    # Elementos menores al pivote
    middle = [x for x in arr if x == pivot] # Elementos iguales al pivote
    right = [x for x in arr if x > pivot]   # Elementos mayores al pivote

    return quick_sort(left) + middle + quick_sort(right)  # Llamadas recursivas

# Ejemplo de uso:
arr = [7, 38, 27, 43, 3, 9, 82, 10]
sorted_arr = quick_sort(arr)
print("Arreglo ordenado:", sorted_arr)
