import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from pathlib import Path
from src.config.settings import RAW_DIR, PROCESSED_DIR, ETI_RESULTS_FILE, setup_logging
import logging

logger = setup_logging("PublicationSpatial")
FIG_DIR = Path("manuscript/figures")
FIG_DIR.mkdir(exist_ok=True, parents=True)

# Strict Wilke-compliant Matplotlib Configuration
plt.rcParams.update({
    'font.size': 14,
    'axes.titlesize': 18,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 12,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.family': 'sans-serif', # Wilke prefers sans-serif for clean viz
    'axes.spines.top': False,    # Remove chart junk
    'axes.spines.right': False,  # Remove chart junk
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.color': '#CCCCCC',
    'axes.axisbelow': True
})

def generate_choropleths():
    logger.info("Generating Wilke-compliant Spatial Maps...")
    try:
        # 1. Load Data
        results = pd.read_csv(PROCESSED_DIR / ETI_RESULTS_FILE)
        results['msoa21cd'] = results['msoa21cd'].astype(str).str.strip().str.upper()
        results = results[results['msoa21cd'].str.startswith('E')].copy() # England only
        
        bayesian_results = pd.read_csv(PROCESSED_DIR / "national_bayesian_results.csv")
        bayesian_results['msoa21cd'] = bayesian_results['msoa21cd'].astype(str).str.strip().str.upper()
        bayesian_results = bayesian_results[bayesian_results['msoa21cd'].str.startswith('E')].copy()
        
        # Load Geometry
        boundaries_path = RAW_DIR / "spatial" / "msoa dec 2021 boundaries.gpkg"
        gdf = gpd.read_file(boundaries_path)
        code_col = 'MSOA21CD' if 'MSOA21CD' in gdf.columns else [c for c in gdf.columns if 'CD' in c.upper()][0]
        gdf[code_col] = gdf[code_col].astype(str).str.strip().str.upper()
        gdf = gdf[gdf[code_col].str.startswith('E')].copy()
        
        # Merge
        msoa_map = gdf.merge(results, left_on=code_col, right_on='msoa21cd', how='inner')
        msoa_map_res = gdf.merge(bayesian_results, left_on=code_col, right_on='msoa21cd', how='inner')
        
        # WILKE RULE: Use Binned/Discrete Color Scales (quantiles, 5 bins) for maps
        
        # Figure 1: Thermal Requirement Map
        fig, ax = plt.subplots(1, 1, figsize=(10, 14))
        # Use a perceptually uniform sequential colormap: viridis
        msoa_map.plot(column='empirical_thermal_index', cmap='viridis', scheme='quantiles', k=5, 
                     legend=True, legend_kwds={'loc': 'lower right', 'title': "Thermal Index ($T^*$)\n[kWh/year/household]", 'fontsize': 12},
                     ax=ax, edgecolor='face', linewidth=0.1)
        ax.set_axis_off()
        ax.set_title("National Distribution of Behaviourally-Adjusted Thermal Requirement ($T^*$)", pad=20)
        plt.savefig(FIG_DIR / "spatial_thermal_requirement.png", bbox_inches='tight')
        plt.close()

        # Figure 2: Spatial Residuals Map
        logger.info("Generating Spatial Residuals Map...")
        # WILKE RULE: Meaningful midpoint (0), use diverging colormap that is colourblind safe (PiYG)
        fig, ax = plt.subplots(1, 1, figsize=(10, 14))
        msoa_map_res.plot(column='msoa_effect_mean', cmap='PiYG', scheme='quantiles', k=5, 
                     legend=True, legend_kwds={'loc': 'lower right', 'title': "Spatial Residuals\n[Log-scale kWh]", 'fontsize': 12},
                     ax=ax, edgecolor='face', linewidth=0.1)
        ax.set_axis_off()
        ax.set_title("Spatial Distribution of the Rationing Signature (Residuals)", pad=20)
        plt.savefig(FIG_DIR / "spatial_residuals.png", bbox_inches='tight')
        plt.close()

    except Exception as e:
        logger.error(f"Failed generating maps: {e}")

def generate_hexbin_interaction():
    logger.info("Generating Wilke-compliant Hexbin Interaction Plot...")
    try:
        results = pd.read_csv(PROCESSED_DIR / ETI_RESULTS_FILE)
        results['msoa21cd'] = results['msoa21cd'].astype(str).str.strip().str.upper()
        results = results[results['msoa21cd'].str.startswith('E')].copy()
        
        conf = pd.read_csv(PROCESSED_DIR / "msoa_confounders_national.csv")
        conf['msoa_cd'] = conf['msoa_cd'].astype(str).str.strip().str.upper()
        data = results.merge(conf, left_on='msoa21cd', right_on='msoa_cd')
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # WILKE RULE: No overplotted scatter points. Use hexbins for density.
        hb = ax.hexbin(
            data['theoretical_gas_kwh'], 
            data['empirical_thermal_index'], 
            C=data['income_dep_score'], 
            reduce_C_function=np.mean, # Show mean deprivation in that bin
            gridsize=50, 
            cmap='plasma', 
            mincnt=1
        )
        
        # Colorbar with explicit units
        cb = fig.colorbar(hb, ax=ax)
        cb.set_label('Mean Income Deprivation Score [Index]')
        
        # Trend line
        sns.regplot(x='theoretical_gas_kwh', y='empirical_thermal_index', data=data, 
                    scatter=False, color='#333333', line_kws={'linestyle': '--'}, ax=ax)
        
        # Direct Labeling instead of legend
        ax.text(data['theoretical_gas_kwh'].max() * 0.8, data['empirical_thermal_index'].max() * 0.9, 
                "Trend Line", color='#333333', fontsize=14, weight='bold')

        # WILKE RULE: Include Units in Axis Titles
        ax.set_xlabel("Modelled Physical Requirement [kWh/year/household]")
        ax.set_ylabel("Behaviourally-Adjusted Thermal Requirement ($T^*$) [kWh/year/household]")
        ax.set_title("Structural-Economic Interaction in Energy Consumption")
        
        plt.tight_layout()
        plt.savefig(FIG_DIR / "interaction_hexbin.png", bbox_inches='tight')
        plt.close()
    except Exception as e: 
        logger.error(f"Failed generating hexbin: {e}")

if __name__ == "__main__":
    generate_choropleths()
    generate_hexbin_interaction()
