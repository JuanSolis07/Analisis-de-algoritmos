# huffman.py
import heapq
import math
import json


class NodoHuffman:
    def __init__(self, caracter, frecuencia):
        self.caracter = caracter
        self.frecuencia = frecuencia
        self.izquierda = None
        self.derecha = None

    def __lt__(self, otro):
        return self.frecuencia < otro.frecuencia


def calcular_frecuencias(texto):
    frec = {}
    for c in texto:
        frec[c] = frec.get(c, 0) + 1
    return frec


def construir_arbol(frecuencias):
    heap = [NodoHuffman(c, f) for c, f in frecuencias.items()]
    heapq.heapify(heap)

    while len(heap) > 1:
        izq = heapq.heappop(heap)
        der = heapq.heappop(heap)
        nuevo = NodoHuffman(None, izq.frecuencia + der.frecuencia)
        nuevo.izquierda = izq
        nuevo.derecha = der
        heapq.heappush(heap, nuevo)

    return heap[0]


def generar_codigos(raiz):
    codigos = {}

    def recorrer(nodo, codigo):
        if nodo is None:
            return
        if nodo.caracter is not None:
            codigos[nodo.caracter] = codigo
            return
        recorrer(nodo.izquierda, codigo + "0")
        recorrer(nodo.derecha, codigo + "1")

    recorrer(raiz, "")
    return codigos


def codificar_texto(texto, codigos):
    return "".join(codigos[c] for c in texto)


def decodificar_texto(bits, raiz):
    resultado = []
    nodo = raiz
    for bit in bits:
        nodo = nodo.izquierda if bit == "0" else nodo.derecha
        if nodo.caracter is not None:
            resultado.append(nodo.caracter)
            nodo = raiz
    return "".join(resultado)

def bits_a_bytes(bits):
    # Agregar ceros al final para que la longitud sea múltiplo de 8
    while len(bits) % 8 != 0:
        bits += "0"
    b = bytearray()
    for i in range(0, len(bits), 8):
        byte = bits[i:i + 8]
        b.append(int(byte, 2))
    return bytes(b)


def bytes_a_bits(data):
    return "".join(f"{byte:08b}" for byte in data)


def guardar_comprimido_binario(nombre_archivo, bits, codigos):
    bits_bytes = bits_a_bytes(bits)
    # Guardamos primero el diccionario en JSON, luego los bytes
    codigos_json = json.dumps(codigos).encode("utf-8")
    longitud_json = len(codigos_json)

    with open(nombre_archivo, "wb") as f:
        f.write(longitud_json.to_bytes(4, "big"))  # 4 bytes con tamaño del JSON
        f.write(codigos_json)
        f.write(bits_bytes)


def leer_comprimido_binario(nombre_archivo):
    with open(nombre_archivo, "rb") as f:
        longitud_json = int.from_bytes(f.read(4), "big")
        codigos_json = f.read(longitud_json)
        bits_bytes = f.read()

    codigos = json.loads(codigos_json.decode("utf-8"))
    bits = bytes_a_bits(bits_bytes)
    return bits, codigos


def reconstruir_arbol_desde_codigos(codigos):
    raiz = NodoHuffman(None, 0)
    for caracter, codigo in codigos.items():
        nodo = raiz
        for bit in codigo:
            if bit == "0":
                if nodo.izquierda is None:
                    nodo.izquierda = NodoHuffman(None, 0)
                nodo = nodo.izquierda
            else:
                if nodo.derecha is None:
                    nodo.derecha = NodoHuffman(None, 0)
                nodo = nodo.derecha
        nodo.caracter = caracter
    return raiz


def calcular_eficiencia(texto, bits_codificados):
    original_bits = len(texto) * 8
    comprimido_bits = len(bits_codificados)
    eficiencia = (1 - (comprimido_bits / original_bits)) * 100
    return max(0, eficiencia)