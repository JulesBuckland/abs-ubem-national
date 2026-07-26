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

from src.config.settings import PROCESSED_DIR, BOUNDARIES_PATH

FIG_DIR = Path(__file__).resolve().parents[2] / "manuscript" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Scoped via plt.rc_context() at each plot call, never mutated globally.
_PLOT_RC = {
    "font.size": 14, "axes.titlesize": 20, "axes.labelsize": 18,
    "xtick.labelsize": 14, "ytick.labelsize": 14, "figure.dpi": 200,
    "savefig.dpi": 300, "axes.spines.top": False, "axes.spines.right": False,
}


def _load_national_geometry() -> gpd.GeoDataFrame:
    """England-only MSOA boundaries, keyed by the project's shared BOUNDARIES_PATH."""
    gdf = gpd.read_file(BOUNDARIES_PATH)
    gdf["MSOA21CD"] = gdf["MSOA21CD"].astype(str).str.strip().str.upper()
    return gdf[gdf["MSOA21CD"].str.startswith("E")].copy()


def _save_choropleth(gdf, column, cmap, title, out_path, norm=None, legend_label=None):
    with plt.rc_context(_PLOT_RC):
        fig, ax = plt.subplots(figsize=(10, 10))
        gdf.plot(column=column, cmap=cmap, norm=norm, legend=True, ax=ax,
                 edgecolor="face", linewidth=0.05,
                 legend_kwds={"label": legend_label or column, "shrink": 0.6})
        ax.set_axis_off()
        ax.set_title(title, pad=16)
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)


def make_fig2_national_tstar_map(res: pd.DataFrame, gdf: gpd.GeoDataFrame) -> int:
    """National T* choropleth. Returns the number of MSOAs plotted."""
    merged = gdf.merge(res[["msoa21cd", "T_star_kwh"]], left_on="MSOA21CD", right_on="msoa21cd")
    _save_choropleth(
        merged, "T_star_kwh", "YlOrRd",
        "National Distribution of Thermal Requirement ($T^*$) - England",
        FIG_DIR / "fig2.png",
        legend_label="Behaviorally-Adjusted Thermal Requirement ($T^*$)",
    )
    return len(merged)


def make_fig4_structural_economic_scatter(res: pd.DataFrame) -> int:
    """Structural-economic interaction scatter. Returns the number of points plotted."""
    d = res.dropna(subset=["T_mean", "T_star_kwh", "income_dep_score"])
    with plt.rc_context(_PLOT_RC):
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
    return len(d)


def make_fig5_spatial_residual_map(spat: pd.DataFrame, gdf: gpd.GeoDataFrame) -> int:
    """National spatial-residual choropleth. Returns the number of MSOAs plotted."""
    merged = gdf.merge(spat[["msoa21cd", "effect_mean"]], left_on="MSOA21CD", right_on="msoa21cd")
    lim = float(np.percentile(np.abs(merged["effect_mean"]), 98))
    _save_choropleth(
        merged, "effect_mean", "PRGn",
        "Spatial Distribution of the Rationing Signature (Residuals) - England",
        FIG_DIR / "fig5.png",
        norm=TwoSlopeNorm(0.0, -lim, lim),
        legend_label=r"Spatial Residuals ($\theta + \phi$)",
    )
    return len(merged)


def regenerate() -> None:
    res = pd.read_csv(PROCESSED_DIR / "msoa_unified_results_inla.csv")
    res["msoa21cd"] = res["msoa21cd"].astype(str).str.strip().str.upper()
    spat = pd.read_csv(PROCESSED_DIR / "msoa_spatial_effect_summary_inla.csv")
    spat["msoa21cd"] = spat["msoa21cd"].astype(str).str.strip().str.upper()
    gdf = _load_national_geometry()

    n2 = make_fig2_national_tstar_map(res, gdf)
    n4 = make_fig4_structural_economic_scatter(res)
    n5 = make_fig5_spatial_residual_map(spat, gdf)
    print(f"Regenerated fig2 ({n2} MSOAs), fig4 ({n4} points), fig5 ({n5} MSOAs) -> {FIG_DIR}")


if __name__ == "__main__":
    regenerate()
