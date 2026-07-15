import os

with open("src/analysis/scaling_benchmark.py", "r", encoding="utf-8") as f:
    content = f.read()

node_extract = """    w_subset = libpysal.weights.Queen.from_dataframe(gdf_subset, ids=gdf_subset[code_col].tolist(), silence_warnings=True)
    
    node1, node2 = [], []
    for i, neighbors in w_subset.neighbors.items():
        for j in neighbors:
            if w_subset.id2i[i] < w_subset.id2i[j]:
                node1.append(w_subset.id2i[i])
                node2.append(w_subset.id2i[j])
    node1 = np.array(node1)
    node2 = np.array(node2)"""

content = content.replace("    w_subset = libpysal.weights.Queen.from_dataframe(gdf_subset, ids=gdf_subset[code_col].tolist(), silence_warnings=True)", node_extract)

old_icar = """        # ICAR term using SPARSE edge-list formulation
        phi_raw = pm.ICAR("phi_raw", W=w_subset.sparse.toarray())
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))"""

new_icar = """        # ICAR term using SPARSE edge-list formulation
        phi_raw = pm.Normal("phi_raw", 0, 1, shape=N)
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi[node1] - phi[node2])**2))"""

content = content.replace(old_icar, new_icar)

with open("src/analysis/scaling_benchmark.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed scaling_benchmark.py ICAR.")

