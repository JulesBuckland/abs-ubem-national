import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from pathlib import Path

FIG_DIR = Path("manuscript/figures")
FIG_DIR.mkdir(parents=True, exist_ok=True)

def generate_visionary_visuals():
    print("Generating Visionary Visuals: The Vulnerability Manifold")
    
    df = pd.read_csv("data/processed/visionary_equity_results.csv")
    
    # --- 1. 3D Surface Plot of the Singularity ---
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # We use a subset for clarity in the scatter or use hexbin-like 3D
    # For a visionary look, we'll use a scatter with a color mapping
    sc = ax.scatter(df['z_eti'], df['z_imd'], df['visionary_priority_score'], 
                    c=df['visionary_priority_score'], cmap='magma', s=20, alpha=0.6)
    
    ax.set_xlabel('Physical Requirement (Z-$T^*$)')
    ax.set_ylabel('Income Deprivation (Z-IMD)')
    ax.set_zlabel('Visionary Priority Score')
    ax.set_title('The Entropic Equity Singularity: Topological Mapping of the Age-Built-Form Paradox')
    
    plt.colorbar(sc, label='Priority Intensity')
    plt.savefig(FIG_DIR / "visionary_manifold_3d.png", dpi=300)
    plt.close()
    
    # --- 2. Phase Transition Map (Entropy vs Priority) ---
    plt.figure(figsize=(12, 8))
    sns.jointplot(x='epistemic_entropy', y='visionary_priority_score', data=df, 
                  kind="hex", color="#4CB391", space=0)
    plt.suptitle("Phase Transition: Information Entropy as a Driver of Equity", y=1.02)
    plt.savefig(FIG_DIR / "visionary_entropy_phase_map.png", dpi=300)
    plt.close()
    
    # --- 3. Linear vs Visionary Conflict Plot ---
    plt.figure(figsize=(10, 8))
    plt.scatter(df['linear_rank'], df['visionary_rank'], c=df['visionary_priority_score'], 
                cmap='viridis', alpha=0.3, s=10)
    plt.plot([0, 7000], [0, 7000], 'r--', alpha=0.5) # Identity line
    plt.xlabel('Linear Rank (Traditional)')
    plt.ylabel('Visionary Rank (Entropic)')
    plt.title('The Structural Contradiction: Divergence between Linear and Topological Prioritization')
    plt.savefig(FIG_DIR / "visionary_rank_conflict.png", dpi=300)
    plt.close()

    print(f"Visionary figures saved to {FIG_DIR}")

if __name__ == "__main__":
    generate_visionary_visuals()
