import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import spearmanr

PROCESSED_DIR = Path(r"C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\data\processed")
FIGURES_DIR = Path(r"C:\Users\jules\OneDrive - The University of Manchester\Internships\projects\energy\paper 5\manuscript\figures")

def main():
    # Load the validation data you already generated
    epc_file = PROCESSED_DIR / "msoa_epc_validation.csv"
    if not epc_file.exists():
        print(f"Error: {epc_file} not found.")
        return
        
    df = pd.read_csv(epc_file)
    
    # We expect columns related to T* (T_star_kwh) and EPC/poor condition
    # Let's inspect the columns to find the right ones
    print(f"Columns available: {df.columns.tolist()}")
    
    # Assuming 'T_star_mean' or similar and 'poor_condition_rate' or similar
    # We will pick the first column that has 'T' and 'mean' or 'star' and the DLUHC proxy
    x_col = 'empirical_thermal_index'
    y_col = 'Housing in poor condition indicator'
    
    df = df.dropna(subset=[x_col, y_col])
    
    corr, p = spearmanr(df[x_col], df[y_col])
    print(f"Spearman correlation: {corr:.3f} (p={p:.2e})")
    
    # Plot
    plt.figure(figsize=(10, 8))
    sns.regplot(
        x=df[x_col], 
        y=df[y_col], 
        scatter_kws={'alpha': 0.3, 's': 15, 'color': '#2c3e50'}, 
        line_kws={'color': '#e74c3c', 'linewidth': 2}
    )
    
    plt.title(f"Divergence from Theoretical Models:\nEmpirical Structural Deficit (T*) vs. DLUHC Poor Housing Proxy\nSpearman $\\rho$ = {corr:.3f} (N={len(df)})", fontsize=14, pad=15)
    plt.xlabel("Behaviorally-Adjusted Thermal Requirement ($T^*$, kWh/year)", fontsize=12)
    plt.ylabel("DLUHC 'Poor Condition' Housing Rate (%)", fontsize=12)
    
    # Clean up aesthetics
    sns.despine()
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    
    out_path = FIGURES_DIR / "fig7_epc_divergence.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"Saved validation plot to {out_path}")

if __name__ == "__main__":
    main()
