import heapq


#Grafo ponderado no dirigido con 6 nodos y 9 aristas
grafo = {
    'A': [('B',4),('C',2)],
    'B': [('A',4),('C',1),('D',5)],
    'C': [('A',2),('B',1),('D',8),('E',10)],
    'D': [('B',5),('C',8),('E',2),('F',6)],
    'E': [('C',10),('D',2),('F',3)],
    'F': [('D',6),('E',3)]
}


#Algoritmo de prim con heapq
def prim(grafo,start= 'A'):
    visitado = set()
    min_heap = [(0,start,None)]
    mst_aristas = []
    peso_total = 0  


    while min_heap and len(visitado) < len(grafo):
        peso,nodo,prev = heapq.heappop(min_heap)
       
        if nodo in visitado:
            continue


        visitado.add(nodo)


        if prev is not None:
            mst_aristas.append((prev,nodo,peso))
            peso_total += peso


        for vecino, w in grafo[nodo]:
            if vecino not in visitado:
                heapq.heappush(min_heap,(w,vecino,nodo))


    return mst_aristas,peso_total




#Union-Find
class Unionfind:
    def __init__(self,nodos):
        self.parent = {x: x for x in nodos}
        self.rank = {x: 0 for x in nodos}


    def find(self,x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
   
    def union(self,a,b):
        rootA = self.find(a)
        rootB = self.find(b)


        if rootA == rootB:
            return False
       
        if self.rank[rootA] < self.rank[rootB]:
            self.parent[rootA] = rootB
        elif self.rank[rootA] > self.rank[rootB]:
            self.parent[rootB] = rootA
        else:
            self.parent[rootB] = rootA
            self.rank[rootA] += 1


        return True




#Algoritmo de Kruskal
def kruskal(grafo):
    aristas = []


    for u in grafo:
        for v,w in grafo[u]:
            if (v,u,w) not in aristas:
                aristas.append((u,v,w))  


    aristas.sort(key= lambda x: x[2])


    uf = Unionfind(grafo.keys())
    mst_aristas = []
    peso_total= 0


    for u,v,w in aristas:
        if uf.union(u,v):
            mst_aristas.append((u,v,w))
            peso_total += w


    return mst_aristas, peso_total




#Algoritmo de Dijkstra
def dijkstra(graph,start = 'A'):
    distancia = {nodo: float('inf') for nodo in graph}
    distancia[start] = 0
    min_heap = [(0,start)]


    while min_heap:
        distancia_actual, nodo = heapq.heappop(min_heap)


        if distancia_actual > distancia[nodo]:
            continue


        for vecino, w in graph[nodo]:  
            distancia_nueva = distancia_actual + w


            if distancia_nueva < distancia[vecino]:  
                distancia[vecino] = distancia_nueva
                heapq.heappush(min_heap,(distancia_nueva,vecino))


    return distancia




#MAIN
if __name__ == "__main__":
    print("Algoritmo de Prim con heapq")
    prim_aristas, prim_peso = prim(grafo,'A')
    for u,v,w in prim_aristas:
        print(f"{u} - {v}: {w}")
    print(f"Peso total del MST con Prim: {prim_peso}\n")


    print("Algoritmo de Kruskal con UnionFind")
    kruskal_aristas, kruskal_peso = kruskal(grafo)
    for u,v,w in kruskal_aristas:
        print(f"{u} - {v}: {w}")
    print(f"Peso total del MST con Kruskal: {kruskal_peso}\n")


    print("Algoritmo de Dijkstra desde A")
    distancia = dijkstra(grafo,'A')
    for nodo in distancia:
        print(f"Distancia minima de A a {nodo}: {distancia[nodo]}")