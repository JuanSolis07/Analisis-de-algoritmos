import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Importar UMAP en lugar de TSNE
import umap.umap_ as umap
from sklearn.cluster import KMeans
from PIL import Image


CSV_PATH = r"C:\Users\USER\OneDrive\Escritorio\Analisis de Algoritmos\Act_03_Clustering\fashion-mnist_test.csv"


try:
    df = pd.read_csv(CSV_PATH)
    print("Dataset cargado. Dimensiones:", df.shape)
except FileNotFoundError:
    print(f"ERROR: No se encontró el archivo en la ruta: {CSV_PATH}")
    print("Por favor, verifica la ruta y el nombre del archivo.")
    exit() # Sale del programa si no encuentra el archivo


# Separar características y etiquetas
X = df.iloc[:, 1:].values
y = df.iloc[:, 0].values


LABEL_NAMES = [
    "T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
    "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"
]


# FILTRAR CLASE 'Shirt' (6)
cluster_objetivo = 6  # Shirt
mask = y == cluster_objetivo
subset_X = X[mask]
subset_y = y[mask]
print(f"Muestras de '{LABEL_NAMES[cluster_objetivo]}': {subset_X.shape[0]}")


# ----------------------------------------------------
# REDUCCIÓN DE DIMENSIONALIDAD CON UMAP
# ----------------------------------------------------
print("Ejecutando UMAP sobre las camisas...")
reducer = umap.UMAP(
    n_components=2,
    random_state=42,
    n_neighbors=15,  # Puedes experimentar con 10, 15, 30
    min_dist=0.1      # Puedes experimentar con 0.0, 0.1, 0.5
)
X_2d = reducer.fit_transform(subset_X)


# ----------------------------------------------------
# DETECCIÓN DE SUBCLUSTERS (KMeans)
# ----------------------------------------------------
# Aplicamos KMeans sobre la representación 2D de UMAP
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
subcluster_labels = kmeans.fit_predict(X_2d)


plt.figure(figsize=(7,6))
# Usamos un 'scatter plot' para visualizar los subclusters
plt.scatter(X_2d[:,0], X_2d[:,1], c=subcluster_labels, cmap='tab10', s=15, alpha=0.7)
plt.title(f"Subclusters dentro de '{LABEL_NAMES[cluster_objetivo]}' (proyección UMAP)")
plt.xlabel("Componente UMAP 1")
plt.ylabel("Componente UMAP 2")
plt.colorbar(ticks=range(3), label='Subcluster ID')
plt.grid(True, linestyle='--', alpha=0.5)
plt.show() #


# ----------------------------------------------------
# VISUALIZAR EJEMPLOS DE SUBCLUSTERS
# ----------------------------------------------------
print("\nVisualizando ejemplos de imágenes por subcluster...")
for sc in np.unique(subcluster_labels):
    # Encontrar hasta 5 índices aleatorios para una mejor representación
    indices_todos = np.where(subcluster_labels == sc)[0]
    # Selecciona 5 índices aleatorios (o menos si hay menos de 5)
    num_ejemplos = min(5, len(indices_todos))
    indices = np.random.choice(indices_todos, size=num_ejemplos, replace=False)


    fig, axes = plt.subplots(1, len(indices), figsize=(2 * len(indices), 2))
   
    # Asegurarse de que 'axes' es iterable incluso si solo hay un índice
    if len(indices) == 1:
        axes = [axes]


    for ax, idx in zip(axes, indices):
        # La imagen es de 28x28 píxeles
        ax.imshow(subset_X[idx].reshape(28,28), cmap='gray')
        ax.axis('off')
   
    plt.suptitle(f"Ejemplos del Subcluster {sc} ({LABEL_NAMES[cluster_objetivo]})", fontsize=14)
    plt.show()