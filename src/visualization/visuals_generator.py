import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
from pathlib import Path
from src.config.settings import RAW_DIR, PROCESSED_DIR, ETI_RESULTS_FILE, setup_logging
import logging

# --- CONFIG ---
logger = setup_logging("NationalVisuals")
FIG_DIR = Path("manuscript/figures")
FIG_DIR.mkdir(exist_ok=True, parents=True)

# Standardize plot style for publication
plt.rcParams.update({
    'font.size': 14,
    'axes.titlesize': 18,
    'axes.labelsize': 16,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 14,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.family': 'serif'
})

def generate_map_figures():
    logger.info("Generating National Thermal Requirement, Uncertainty, and Residual Maps (England-only)...")
    try:
        results = pd.read_csv(PROCESSED_DIR / ETI_RESULTS_FILE)
        results['msoa21cd'] = results['msoa21cd'].astype(str).str.strip().str.upper()
        # FILTER FOR ENGLAND
        results = results[results['msoa21cd'].str.startswith('E')].copy()
        
        # Load Bayesian results for residuals and uncertainty
        bayesian_results = pd.read_csv(PROCESSED_DIR / "national_bayesian_results.csv")
        bayesian_results['msoa21cd'] = bayesian_results['msoa21cd'].astype(str).str.strip().str.upper()
        # FILTER FOR ENGLAND
        bayesian_results = bayesian_results[bayesian_results['msoa21cd'].str.startswith('E')].copy()
        
        # Load boundaries
        boundaries_path = RAW_DIR / "spatial" / "msoa dec 2021 boundaries.gpkg"
        gdf = gpd.read_file(boundaries_path)
        code_col = 'MSOA21CD' if 'MSOA21CD' in gdf.columns else [c for c in gdf.columns if 'CD' in c.upper()][0]
        gdf[code_col] = gdf[code_col].astype(str).str.strip().str.upper()
        gdf = gdf[gdf[code_col].str.startswith('E')].copy()
        
        msoa_map = gdf.merge(results, left_on=code_col, right_on='msoa21cd', how='inner')
        msoa_map_res = gdf.merge(bayesian_results, left_on=code_col, right_on='msoa21cd', how='inner')
        
        # Figure 2: National Distribution Map
        vmin_tstar = np.nanpercentile(msoa_map['empirical_thermal_index'], 1)
        vmax_tstar = np.nanpercentile(msoa_map['empirical_thermal_index'], 99)
        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        msoa_map.plot(column='empirical_thermal_index', cmap='YlOrRd', legend=True, 
                     legend_kwds={'label': "Behaviorally-Adjusted Thermal Requirement ($T^*$)", 'orientation': "vertical", 'shrink': 0.6},
                     ax=ax, edgecolor='face', linewidth=0.1, vmin=vmin_tstar, vmax=vmax_tstar)
        ax.set_axis_off()
        ax.set_title("National Distribution of Thermal Requirement ($T^*$) - England", pad=20)
        plt.savefig(FIG_DIR / "fig2.png", bbox_inches='tight'); plt.close()
        # Figure 3: Bayesian Uncertainty Map (3.17x Calibrated)
        logger.info("Generating Calibrated Uncertainty Map (Figure 3)...")
        # Apply the 3.17x multiplier to the SD
        msoa_map_res['calibrated_sd'] = msoa_map_res['msoa_effect_sd'] * 3.17

        plot_col = 'calibrated_sd'
        vmin_sd = np.nanpercentile(msoa_map_res[plot_col], 1)
        vmax_sd = np.nanpercentile(msoa_map_res[plot_col], 99)

        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        msoa_map_res.plot(column=plot_col, cmap='magma', legend=True,
                         legend_kwds={'label': "Calibrated Posterior Standard Deviation (3.17x multiplier)", 'orientation': "vertical", 'shrink': 0.6},
                         ax=ax, edgecolor='face', linewidth=0.1, vmin=vmin_sd, vmax=vmax_sd)
        ax.set_axis_off()
        ax.set_title("Bayesian Uncertainty of Thermal Estimates - England", pad=20)
        plt.savefig(FIG_DIR / "fig3.png", bbox_inches='tight'); plt.close()
        # Figure 5 (in text) / fig5.png: Spatial Residuals Map (Now Hexbin density handled in other function or renamed)
        # Actually let's keep fig5 as the Spatial Residuals Map but maybe make it a hexbin if it's overplotted?
        # No, fig5 is a map, overplotting is for scatter.
        logger.info("Generating Spatial Residuals Map (Figure 5)...")
        vmax_resid = np.nanpercentile(msoa_map_res['msoa_effect_mean'].abs(), 99)
        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        msoa_map_res.plot(column='msoa_effect_mean', cmap='PRGn', legend=True,
                     legend_kwds={'label': "Spatial Residuals (theta + phi)", 'orientation': "vertical", 'shrink': 0.6},
                     ax=ax, edgecolor='face', linewidth=0.1, vmin=-vmax_resid, vmax=vmax_resid)
        ax.set_axis_off()
        ax.set_title("Spatial Distribution of the Rationing Signature (Residuals) - England", pad=20)
        plt.savefig(FIG_DIR / "fig5.png", bbox_inches='tight'); plt.close()

    except Exception as e:
        logger.error(f"Map Figures: {e}")

def generate_interaction_plot():
    logger.info("Generating Structural-Economic Interaction Plot (Hexbin Density)...")
    try:
        results = pd.read_csv(PROCESSED_DIR / ETI_RESULTS_FILE)
        results['msoa21cd'] = results['msoa21cd'].astype(str).str.strip().str.upper()
        results = results[results['msoa21cd'].str.startswith('E')].copy()
        
        conf = pd.read_csv(PROCESSED_DIR / "msoa_confounders_national.csv")
        conf['msoa_cd'] = conf['msoa_cd'].astype(str).str.strip().str.upper()
        data = results.merge(conf, left_on='msoa21cd', right_on='msoa_cd')
        
        plt.figure(figsize=(10, 8))
        
        sc = plt.scatter(
            data['theoretical_gas_kwh'], 
            data['empirical_thermal_index'], 
            c=data['income_dep_score'], 
            cmap='magma_r',
            alpha=0.6,
            s=15,
            edgecolors='none'
        )
        plt.colorbar(sc, label='Income Deprivation Score')
        
        # Trend line
        sns.regplot(x='theoretical_gas_kwh', y='empirical_thermal_index', data=data, 
                    scatter=False, color='black', line_kws={'linestyle': '--'}, label='Trend')
        
        plt.xlabel("Modelled Physical Requirement (kWh/year)")
        plt.ylabel("Behaviorally-Adjusted Thermal Requirement ($T^*$)")
        plt.title("Structural-Economic Interaction (Hexbin Density)")
        
        plt.tight_layout()
        plt.savefig(FIG_DIR / "fig4.png", bbox_inches='tight')
        plt.savefig(FIG_DIR / "interaction_kde.png", bbox_inches='tight')
        plt.close()
    except Exception as e: logger.error(f"Interaction Plot: {e}")

if __name__ == "__main__":
    generate_map_figures()
    generate_interaction_plot()
