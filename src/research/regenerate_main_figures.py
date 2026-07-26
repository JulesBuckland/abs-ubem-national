"""Regenerate the main-text figures (fig2, fig4, fig5) from the current national
INLA outputs, so the published maps always reflect the primary inference engine.

    fig2 -- national choropleth of the behaviorally-adjusted requirement T*
    fig4 -- structural-economic interaction (modelled physical requirement vs T*,
            coloured by income deprivation)
    fig5 -- national choropleth of the RSR-projected spatial residual (theta+phi)

Run from the project root:
    python -m src.research.regenerate_main_figures
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[2]
PROC = ROOT / "data" / "processed"
SHP = ROOT / "data" / "raw" / "spatial" / "MSOA_2021_EW_BGC_V3.shp"
FIG_DIR = ROOT / "manuscript" / "figures"

plt.rcParams.update({
    "font.size": 14, "axes.titlesize": 20, "axes.labelsize": 18,
    "xtick.labelsize": 14, "ytick.labelsize": 14, "figure.dpi": 200,
    "savefig.dpi": 300, "axes.spines.top": False, "axes.spines.right": False,
})


def _england(gdf, code_col):
    return gdf[gdf[code_col].str.startswith("E")].copy()


def regenerate():
    res = pd.read_csv(PROC / "msoa_unified_results_inla.csv")
    res["msoa21cd"] = res["msoa21cd"].astype(str).str.strip().str.upper()
    spat = pd.read_csv(PROC / "msoa_spatial_effect_summary_inla.csv")
    spat["msoa21cd"] = spat["msoa21cd"].astype(str).str.strip().str.upper()

    gdf = gpd.read_file(SHP)
    code_col = "MSOA21CD" if "MSOA21CD" in gdf.columns else next(
        c for c in gdf.columns if "CD" in c.upper())
    gdf[code_col] = gdf[code_col].astype(str).str.strip().str.upper()
    gdf = _england(gdf, code_col)

    # fig2: national T* choropleth
    m2 = gdf.merge(res[["msoa21cd", "T_star_kwh"]], left_on=code_col, right_on="msoa21cd")
    fig, ax = plt.subplots(figsize=(10, 10))
    m2.plot(column="T_star_kwh", cmap="YlOrRd", legend=True, ax=ax,
            edgecolor="face", linewidth=0.05,
            legend_kwds={"label": "Behaviorally-Adjusted Thermal Requirement ($T^*$)", "shrink": 0.6})
    ax.set_axis_off()
    ax.set_title("National Distribution of Thermal Requirement ($T^*$) - England", pad=16)
    fig.savefig(FIG_DIR / "fig2.png", bbox_inches="tight")
    plt.close(fig)

    # fig4: structural-economic interaction
    d = res.dropna(subset=["T_mean", "T_star_kwh", "income_dep_score"])
    fig, ax = plt.subplots(figsize=(10, 8))
    sc = ax.scatter(d["T_mean"], d["T_star_kwh"], c=d["income_dep_score"], cmap="magma_r",
                    s=9, alpha=0.7, vmin=0, vmax=d["income_dep_score"].quantile(0.99))
    fig.colorbar(sc, ax=ax).set_label("Income Deprivation Score")
    b1, b0 = np.polyfit(d["T_mean"], d["T_star_kwh"], 1)
    xs = np.linspace(d["T_mean"].min(), d["T_mean"].max(), 100)
    ax.plot(xs, b0 + b1 * xs, "--", color="black", linewidth=2.2)
    ax.set_xlabel("Modelled Physical Requirement (kWh/year)")
    ax.set_ylabel("Behaviorally-Adjusted Thermal Requirement ($T^*$)")
    ax.set_title("Structural-Economic Interaction")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig4.png", bbox_inches="tight")
    plt.close(fig)

    # fig5: spatial residual choropleth (diverging, centred at 0)
    m5 = gdf.merge(spat[["msoa21cd", "effect_mean"]], left_on=code_col, right_on="msoa21cd")
    lim = float(np.percentile(np.abs(m5["effect_mean"]), 98))
    fig, ax = plt.subplots(figsize=(10, 10))
    m5.plot(column="effect_mean", cmap="PRGn", norm=TwoSlopeNorm(0.0, -lim, lim),
            legend=True, ax=ax, edgecolor="face", linewidth=0.05,
            legend_kwds={"label": r"Spatial Residuals ($\theta + \phi$)", "shrink": 0.6})
    ax.set_axis_off()
    ax.set_title("Spatial Distribution of the Rationing Signature (Residuals) - England", pad=16)
    fig.savefig(FIG_DIR / "fig5.png", bbox_inches="tight")
    plt.close(fig)

    print(f"Regenerated fig2/fig4/fig5 for {len(m2)} MSOAs -> {FIG_DIR}")


if __name__ == "__main__":
    regenerate()
