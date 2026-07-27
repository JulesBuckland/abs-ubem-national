"""Build the graphical abstract required by Energy and Buildings at submission.

Elsevier's spec: at least 531 x 1328 px (h x w), legible at 5 x 13 cm, so the
canvas here is that ratio at 2x. Three panels read left to right as the paper's
argument: metered demand misreads deprived stock, the model separates physics
from rationing, and the result is a national structural map.

The right-hand panel is drawn from the real national INLA output rather than
mocked up, so the abstract cannot show a different England than Figure 2 does.

Run from the project root:
    python -m src.research.make_graphical_abstract
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import geopandas as gpd

from src.config.settings import PROCESSED_DIR, BOUNDARIES_PATH

FIG_DIR = Path(__file__).resolve().parents[2] / "manuscript" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

OUT_PATH = FIG_DIR / "graphical_abstract.tif"
RESULTS_PATH = PROCESSED_DIR / "msoa_unified_results_inla.csv"

# 1328 x 531 px at Elsevier's minimum; drawn at 2x for print legibility.
FIG_W_IN, FIG_H_IN = 13.28, 5.31
DPI = 200

_PLOT_RC = {"font.size": 11, "figure.dpi": DPI, "savefig.dpi": DPI}


def load_national_tstar() -> gpd.GeoDataFrame:
    """England MSOA geometries joined to the primary INLA T* estimates."""
    res = pd.read_csv(RESULTS_PATH, usecols=["msoa21cd", "T_star_kwh"])
    gdf = gpd.read_file(BOUNDARIES_PATH)
    gdf["MSOA21CD"] = gdf["MSOA21CD"].astype(str).str.strip().str.upper()
    gdf = gdf[gdf["MSOA21CD"].str.startswith("E")]
    return gdf.merge(res, left_on="MSOA21CD", right_on="msoa21cd")


def _panel_problem(ax) -> None:
    """Left panel: the performance gap that motivates the method."""
    ax.set_axis_off()
    ax.set_title("The problem", fontweight="bold", fontsize=13, pad=8)
    ax.text(0.5, 0.80, "Deprived households\nration heat",
            ha="center", va="center", fontsize=11.5, transform=ax.transAxes)
    ax.annotate("", xy=(0.5, 0.56), xytext=(0.5, 0.70),
                xycoords=ax.transAxes, textcoords=ax.transAxes,
                arrowprops=dict(facecolor="black", width=1.4, headwidth=8, shrink=0.02))
    ax.text(0.5, 0.46, "Metered demand looks\nLOW", ha="center", va="center",
            fontsize=11.5, fontweight="bold", color="#b71c1c", transform=ax.transAxes)
    ax.text(0.5, 0.24, "Cold, leaky homes are\nscored as efficient and\nmissed by targeting",
            ha="center", va="center", fontsize=10.5, style="italic",
            color="#444444", transform=ax.transAxes)


def _panel_method(ax, n_msoas: int, n_households: int) -> None:
    """Middle panel: what the framework actually does."""
    ax.set_axis_off()
    ax.set_title("The method", fontweight="bold", fontsize=13, pad=8)
    boxes = [
        ("UBEM archetype physics\n(theoretical need $T_h$)", 0.78, "#fff3e0"),
        ("Hierarchical Bayesian model\nBYM2 spatial prior, R-INLA", 0.50, "#ffebee"),
        ("Restricted Spatial Regression\nseparates rationing from fabric", 0.22, "#e3f2fd"),
    ]
    for text, y, color in boxes:
        ax.text(0.5, y, text, ha="center", va="center", fontsize=10.2,
                fontweight="bold", transform=ax.transAxes,
                bbox=dict(boxstyle="round,pad=0.45", facecolor=color, edgecolor="black"))
    for y0, y1 in [(0.70, 0.60), (0.42, 0.32)]:
        ax.annotate("", xy=(0.5, y1), xytext=(0.5, y0),
                    xycoords=ax.transAxes, textcoords=ax.transAxes,
                    arrowprops=dict(facecolor="black", width=1.4, headwidth=8, shrink=0.02))
    ax.text(0.5, 0.04, f"{n_households:,} households  |  {n_msoas:,} MSOAs",
            ha="center", va="center", fontsize=9.5, color="#333333",
            transform=ax.transAxes)


def _panel_result(ax, merged: gpd.GeoDataFrame) -> None:
    """Right panel: the national T* map from the primary INLA fit."""
    ax.set_title("The result", fontweight="bold", fontsize=13, pad=8)
    merged.plot(column="T_star_kwh", cmap="YlOrRd", ax=ax,
                edgecolor="face", linewidth=0.02, legend=True,
                legend_kwds={"label": "$T^*$ (kWh/year)", "shrink": 0.72})
    ax.set_axis_off()
    ax.text(0.5, -0.02, "Behaviorally-adjusted structural requirement",
            ha="center", va="top", fontsize=10, transform=ax.transAxes)


def build(out_path: Path = OUT_PATH) -> Path:
    merged = load_national_tstar()
    n_households = len(pd.read_parquet(
        PROCESSED_DIR / "national_synthetic_population_eti.parquet",
        columns=["msoa21cd"]))

    with plt.rc_context(_PLOT_RC):
        fig, axes = plt.subplots(1, 3, figsize=(FIG_W_IN, FIG_H_IN),
                                 gridspec_kw={"width_ratios": [1.0, 1.15, 1.25]})
        _panel_problem(axes[0])
        _panel_method(axes[1], len(merged), n_households)
        _panel_result(axes[2], merged)
        fig.suptitle(
            "Decoupling building physics from socioeconomic rationing at national scale",
            fontweight="bold", fontsize=14, y=0.98)
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        fig.savefig(out_path, format="tiff", bbox_inches="tight",
                    pil_kwargs={"compression": "tiff_lzw"})
        plt.close(fig)

    print(f"Graphical abstract written to {out_path}")
    return out_path


if __name__ == "__main__":
    build()
