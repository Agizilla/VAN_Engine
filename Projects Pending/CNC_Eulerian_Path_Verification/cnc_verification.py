import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import networkx as nx

def load_landmarks_from_csv(csv_path, x_col='X', y_col='Y', z_col='Z', label_col='Label'):
    df = pd.read_csv(csv_path)
    coords = df[[x_col, y_col, z_col]].values
    labels = df[label_col].values
    return labels, coords

def build_graph_from_proximity(coords, k_neighbors=4, max_dist=0.15):
    tree = cKDTree(coords)
    edges = set()
    for i, coord in enumerate(coords):
        distances, indices = tree.query(coord, k=k_neighbors+1)
        for j, dist in zip(indices[1:], distances[1:]):
            if dist <= max_dist:
                u, v = sorted((i, j))
                edges.add((u, v))
    return list(edges)

def check_connectivity(n_nodes, edges):
    G = nx.Graph()
    G.add_nodes_from(range(n_nodes))
    G.add_edges_from(edges)
    components = list(nx.connected_components(G))
    if len(components) == 1:
        print("✓ Graph fully connected")
        return True, G
    else:
        print(f"✗ {len(components)} components")
        return False, G

def check_eulerian_path_possible(G):
    degrees = dict(G.degree())
    odd = [n for n, d in degrees.items() if d % 2 == 1]
    if len(odd) == 0:
        print("✓ Eulerian circuit exists")
        return True, "circuit"
    elif len(odd) == 2:
        print(f"✓ Eulerian path exists ({odd[0]} → {odd[1]})")
        return True, "path"
    else:
        print(f"✗ {len(odd)} odd-degree vertices")
        return False, None

def check_path_continuity(seq, coords, tol=0.05):
    violations = []
    for i in range(len(seq)-1):
        d = np.linalg.norm(coords[seq[i]] - coords[seq[i+1]])
        if d > tol:
            violations.append((seq[i], seq[i+1], d))
            print(f"✗ {seq[i]}→{seq[i+1]} : {d:.4f} > {tol}")
    return len(violations) == 0

if __name__ == "__main__":
    # labels, coords = load_landmarks_from_csv("landmarks.csv")
    # edges = build_graph_from_proximity(coords)
    # _, G = check_connectivity(len(labels), edges)
    # check_eulerian_path_possible(G)
    # check_path_continuity(list(range(468)), coords, 0.05)
    pass
