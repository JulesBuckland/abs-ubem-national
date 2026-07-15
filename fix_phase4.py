import os

# 1. main.py
main_content = """import os
import sys

from src.inference.model_unified import run_national_unified_model

def main():
    print("==================================================")
    print("ABS-UBEM Production Runner (National Graph)")
    print("==================================================")
    run_national_unified_model()

if __name__ == "__main__":
    main()
"""
with open("main.py", "w", encoding="utf-8") as f:
    f.write(main_content)

# 2. src/inference/model_unified.py
with open("src/inference/model_unified.py", "r", encoding="utf-8") as f:
    content = f.read()

old_icar_unified = """        phi_raw = pm.ICAR("phi_raw", W=w.sparse.toarray())
        
        # Zero-mean centering (same as before)
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))"""

new_icar_unified = """        phi_raw = pm.Normal("phi_raw", 0, 1, shape=N)
        
        # Zero-mean centering (same as before)
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi[node1] - phi[node2])**2))"""

if old_icar_unified in content:
    content = content.replace(old_icar_unified, new_icar_unified)
    with open("src/inference/model_unified.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed model_unified.py ICAR.")

# 3. src/analysis/run_competitors.py
with open("src/analysis/run_competitors.py", "r", encoding="utf-8") as f:
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

old_icar_comp = """        phi_raw = pm.ICAR("phi_raw", W=w_subset.sparse.toarray())
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))"""

new_icar_comp = """        phi_raw = pm.Normal("phi_raw", 0, 1, shape=N)
        phi = pm.Deterministic("phi", phi_raw - pm.math.mean(phi_raw))
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi[node1] - phi[node2])**2))"""

content = content.replace(old_icar_comp, new_icar_comp)

with open("src/analysis/run_competitors.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed run_competitors.py ICAR.")

# 4. tests/inference/test_nuts.py
with open("tests/inference/test_nuts.py", "r", encoding="utf-8") as f:
    content = f.read()

old_advi = """        # Inference (ADVI due to size, but unified across 6840 MSOAs!)
        logger.info("Starting Variational Inference (ADVI) on full graph...")
        log_memory("Pre-ADVI Memory Peak")
        mean_field = pm.fit(n=30000, method='advi', obj_optimizer=pm.adam(learning_rate=0.01))
        trace = mean_field.sample(1000)"""

new_nuts = """        # Inference (NUTS)
        logger.info("Starting NUTS on full graph...")
        log_memory("Pre-NUTS Memory Peak")
        trace = pm.sample(tune=10, draws=10, chains=2, cores=1, progressbar=False)"""

old_icar_nuts = """        phi_raw = pm.Normal("phi_raw", mu=0.0, sigma=1.0, shape=len(msoa_stats))
        phi_centered = phi_raw - pm.math.mean(phi_raw)"""

new_icar_nuts = """        phi_raw = pm.Normal("phi_raw", mu=0.0, sigma=1.0, shape=len(msoa_stats))
        phi_centered = phi_raw - pm.math.mean(phi_raw)
        pm.Potential("icar_penalty", -0.5 * pm.math.sum((phi_centered[node1] - phi_centered[node2])**2))"""

content = content.replace(old_advi, new_nuts)
content = content.replace(old_icar_nuts, new_icar_nuts)

with open("tests/inference/test_nuts.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Fixed test_nuts.py.")

