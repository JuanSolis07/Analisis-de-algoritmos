import itertools


distancias = [
    [0, 2, 5, 7],  
    [2, 0, 8, 3],  
    [5, 8, 0, 1],  
    [7, 3, 1, 0]  
]


def calcular_distancia(orden):
    distancia_total = 0
    for i in range(len(orden) - 1):
        distancia_total += distancias[orden[i]][orden[i+1]]
    distancia_total += distancias[orden[-1]][orden[0]]
    return distancia_total


nodos = ['a', 'b', 'c', 'd']
indices_nodos = [0, 1, 2, 3]
permutaciones = itertools.permutations(indices_nodos[1:])  


distancia_minima = float('inf')
mejores_recorridos = []


for perm in permutaciones:
    recorrido = [0] + list(perm)
    distancia = calcular_distancia(recorrido)
   
    if distancia < distancia_minima:
        distancia_minima = distancia
        mejores_recorridos = [recorrido]
    elif distancia == distancia_minima:
        mejores_recorridos.append(recorrido)


print(f"Distancia mínima: {distancia_minima}")
print("Recorridos con esa distancia:")


for recorrido in mejores_recorridos:
    nombres = [nodos[i] for i in recorrido]
    print(f"  {nombres}")