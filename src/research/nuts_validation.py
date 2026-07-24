import pandas as pd
import numpy as np
import pymc as pm
import logging
from pathlib import Path
import scipy.sparse as sp
from typing import List, Tuple
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import geopandas as gpd
import libpysal

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("NUTS_Validation")

PROCESSED_DIR = Path("data/processed")
RAW_DIR = Path("data/raw")
FIGURES_DIR = Path("manuscript/figures")
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

def bfs_subgraph(adj_dict: dict, start_node: str, size: int) -> List[str]:
    """Extract a contiguous subgraph using Breadth First Search."""
    visited = set()
    queue = [start_node]
    subgraph = []
    
    while queue and len(subgraph) < size:
        node = queue.pop(0)
        if node not in visited:
            visited.add(node)
            subgraph.append(node)
            # Add neighbors
            neighbors = adj_dict.get(node, [])
            for n in neighbors:
                if n not in visited and n not in queue:
                    queue.append(n)
                    
    return subgraph

def run_nuts_subset(subset_msoas: List[str], df: pd.DataFrame, adj_dict: dict, label: str):
    logger.info(f"Preparing NUTS validation for {label} (N={len(subset_msoas)})...")
    
    # Filter data
    df_sub = df[df["msoa_cd"].isin(subset_msoas)].copy()
    df_sub = df_sub.sort_values("msoa_cd").reset_index(drop=True)
    msoa_list = df_sub["msoa_cd"].tolist()
    msoa_to_idx = {m: i for i, m in enumerate(msoa_list)}
    
    # Build subgraph adjacency
    N = len(msoa_list)
    node1, node2 = [], []
    for m in msoa_list:
        neighbors = adj_dict.get(m, [])
        for n in neighbors:
            if n in msoa_to_idx and msoa_to_idx[m] < msoa_to_idx[n]: # undirected
                node1.append(msoa_to_idx[m])
                node2.append(msoa_to_idx[n])
                
    node1 = np.array(node1)
    node2 = np.array(node2)
    
    row = np.concatenate([node1, node2])
    col = np.concatenate([node2, node1])
    data = np.ones(len(row))
    W = sp.csr_matrix((data, (row, col)), shape=(N, N))
    W = W.toarray()
    
    # Standardize using GLOBAL mean and std to ensure coefficients are strictly comparable to ADVI
    global_z_mean = df["income_dep_score"].mean()
    global_z_std = df["income_dep_score"].std()
    
    Z_inc = df_sub["income_dep_score"].values
    Z_inc = (Z_inc - global_z_mean) / global_z_std
    
    y_obs = df_sub["y_mean"].values
    T_obs = df_sub["T_mean"].values
    
    with pm.Model() as model:
        beta_th = pm.Normal("beta_th", mu=-0.3, sigma=0.1)
        beta_inc = pm.Normal("beta_inc", mu=0.0, sigma=0.5)
        
        sigma_spatial = pm.HalfNormal("sigma_spatial", sigma=1.0)
        phi = pm.ICAR("phi", W=W, sigma=sigma_spatial)
        
        sigma_unstruct = pm.HalfNormal("sigma_unstruct", sigma=1.0)
        theta = pm.Normal("theta", mu=0.0, sigma=sigma_unstruct, shape=N)
        
        rho = pm.Beta("rho", alpha=0.5, beta=0.5)
        spatial_effect = pm.Deterministic("spatial_effect", np.sqrt(rho) * phi + np.sqrt(1 - rho) * theta)
        
        mu = np.log(T_obs) + beta_th + beta_inc * Z_inc + spatial_effect
        
        sigma_err = pm.HalfNormal("sigma_err", sigma=0.5)
        corrected_mu = mu - (sigma_err**2 / 2)
        
        y = pm.Normal("y", mu=corrected_mu, sigma=sigma_err, observed=np.log(y_obs))
        
        logger.info(f"Starting exact NUTS sampling for {label}...")
        trace = pm.sample(draws=300, tune=300, cores=2, chains=2, target_accept=0.85, compute_convergence_checks=False)
        
    beta_inc_mean = trace.posterior["beta_inc"].mean().item()
    sigma_err_mean = trace.posterior["sigma_err"].mean().item()
    T_star_nuts = np.exp(np.log(y_obs) - beta_inc_mean * Z_inc + (sigma_err_mean**2) / 2)
    
    df_sub["T_star_nuts"] = T_star_nuts
    return df_sub

def main():
    logger.info("Loading ADVI National Results and Spatial Graph...")
    results_path = PROCESSED_DIR / "msoa_unified_results.csv"
    if not results_path.exists():
        logger.error("National ADVI results not found. Please run 02a first.")
        return
        
    df = pd.read_csv(results_path)
    
    # Generate adj_dict from geopandas
    boundaries_path = RAW_DIR / "spatial" / "msoa dec 2021 boundaries.gpkg"
    gdf = gpd.read_file(boundaries_path)
    w = libpysal.weights.Queen.from_dataframe(gdf, ids=gdf['MSOA21CD'].tolist(), silence_warnings=True)
    adj_dict = w.neighbors
    
    region_df = pd.read_csv(PROCESSED_DIR / "msoa_region_lookup.csv").dropna()
    london_msoas = region_df[region_df["region"] == "London"]["msoa21cd"].tolist()
    nw_msoas = region_df[region_df["region"] == "North West"]["msoa21cd"].tolist()
    sw_msoas = region_df[region_df["region"] == "South West"]["msoa21cd"].tolist()
    
    valid_msoas = set(df["msoa_cd"].tolist())
    london_seed = next(m for m in london_msoas if m in valid_msoas)
    nw_seed = next(m for m in nw_msoas if m in valid_msoas)
    sw_seed = next(m for m in sw_msoas if m in valid_msoas)
    
    SUBSET_SIZE = 150
    subgraph_urban = bfs_subgraph(adj_dict, london_seed, SUBSET_SIZE)
    subgraph_suburb = bfs_subgraph(adj_dict, nw_seed, SUBSET_SIZE)
    subgraph_rural = bfs_subgraph(adj_dict, sw_seed, SUBSET_SIZE)
    
    df_urban = run_nuts_subset(subgraph_urban, df, adj_dict, "Urban (London)")
    df_suburb = run_nuts_subset(subgraph_suburb, df, adj_dict, "Suburban (North West)")
    df_rural = run_nuts_subset(subgraph_rural, df, adj_dict, "Rural (South West)")
    
    val_df = pd.concat([
        df_urban.assign(Typology="Urban"),
        df_suburb.assign(Typology="Suburban"),
        df_rural.assign(Typology="Rural")
    ])
    
    plt.figure(figsize=(15, 5))
    
    for i, (typology, color) in enumerate(zip(["Urban", "Suburban", "Rural"], ["#E63946", "#457B9D", "#2A9D8F"])):
        plt.subplot(1, 3, i+1)
        sub_df = val_df[val_df["Typology"] == typology]
        
        x = sub_df["T_star_kwh"].values # ADVI
        y = sub_df["T_star_nuts"].values # NUTS
        
        r, _ = pearsonr(x, y)
        r2 = r**2
        
        plt.scatter(x, y, alpha=0.6, color=color, s=20)
        
        min_val = min(x.min(), y.min())
        max_val = max(x.max(), y.max())
        plt.plot([min_val, max_val], [min_val, max_val], "k--", alpha=0.5)
        
        plt.title(f"{typology} Validation\n$R^2$ = {r2:.3f}")
        plt.xlabel("ADVI T* (kWh)")
        plt.ylabel("Exact NUTS T* (kWh)")
        plt.grid(True, alpha=0.3)
        
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "cross_typology_validation.png", dpi=300)
    logger.info("Validation completed. Scatterplot saved to manuscript/figures/cross_typology_validation.png")

if __name__ == "__main__":
    main()
