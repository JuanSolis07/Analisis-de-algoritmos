#Programador: Juan Pablo Solís Regín Codigo: 220468416
import numpy as np
from python_tsp.exact import solve_tsp_dynamic_programming

distance_matrix = np.array([
    [15, 40, 33, 11, 29],
    [21, 30, 19, 57, 10],
    [57, 46, 70, 12, 68],
    [74, 49, 38, 25, 34],
    [31, 12, 26, 31, 10]
])

ruta, distancia = solve_tsp_dynamic_programming(distance_matrix)
ruta = np.array(ruta) + 1
print("La ruta final es: ", ruta, "La distancia entre ciudades es: ", distancia)