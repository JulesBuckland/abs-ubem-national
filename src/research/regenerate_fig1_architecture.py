"""Regenerate Figure 1, the system-architecture flowchart.

The previous version of this figure (archive/legacy_scripts/utils/draw_fig1.py)
hardcoded its counts and drifted out of sync with the manuscript: it stated
684,000 households where the synthesized population actually holds 685,300, and
labelled the synthesis step "Deterministic Stratified Expansion" while the text
describes multi-dimensional IPF. It also predated the NUTS->INLA migration and
still named a bare ICAR prior rather than the BYM2/R-INLA primary engine.

Every count drawn here is read from the actual synthetic population, so the
figure cannot silently drift from the data again.

Run from the project root:
    python -m src.research.regenerate_fig1_architecture
"""
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from src.config.settings import PROCESSED_DIR

FIG_DIR = Path(__file__).resolve().parents[2] / "manuscript" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

POPULATION_PATH = PROCESSED_DIR / "national_synthetic_population_eti.parquet"

_PLOT_RC = {"figure.dpi": 200, "savefig.dpi": 300}

# NEED seed size is a property of the source microdata extract, not of any
# derived artifact, so it is stated rather than counted.
NEED_SEED_LABEL = "50k Seed"


def population_counts(path: Path = POPULATION_PATH) -> tuple[int, int]:
    """Return (n_households, n_msoas) read from the synthesized population."""
    df = pd.read_parquet(path, columns=["msoa21cd"])
    return len(df), df["msoa21cd"].nunique()


def build_boxes(n_households: int, n_msoas: int) -> list:
    """Flowchart nodes as [text, x, y, w, h, facecolor], top to bottom."""
    return [
        [f"Administrative Microdata\n(NEED 2024 - {NEED_SEED_LABEL})",
         0.30, 0.90, 0.40, 0.08, "#e1f5fe"],
        ["Multi-Dimensional IPF\n(Property, Age, Tenure, IMD)",
         0.10, 0.75, 0.35, 0.08, "#fff9c4"],
        ["Census 2021 MSOA Marginals\n(Spatial Constraints)",
         0.55, 0.75, 0.35, 0.08, "#e8f5e9"],
        [f"Synthetic Population\n({n_households:,} Household Entities)",
         0.30, 0.60, 0.40, 0.08, "#f3e5f5"],
        ["UBEM Archetype Mapping\n(Theoretical Need $T_h$)",
         0.30, 0.45, 0.40, 0.08, "#fff3e0"],
        [f"MSOA-level Aggregation\n({n_msoas:,} Neighborhoods, Mean Need $T_m$)",
         0.30, 0.30, 0.40, 0.08, "#e0f2f1"],
        ["Hierarchical Bayesian Model\n(BYM2 Spatial Prior, R-INLA)",
         0.30, 0.15, 0.40, 0.08, "#ffebee"],
        ["Behaviorally-Adjusted\nInventory ($T^*$)",
         0.30, 0.00, 0.40, 0.08, "#c8e6c9"],
    ]


# (start, end) in axes coordinates; the final entry is the Census side-feed.
_ARROWS = [
    ((0.50, 0.90), (0.275, 0.83)),
    ((0.275, 0.75), (0.50, 0.68)),
    ((0.50, 0.60), (0.50, 0.53)),
    ((0.50, 0.45), (0.50, 0.38)),
    ((0.50, 0.30), (0.50, 0.23)),
    ((0.50, 0.15), (0.50, 0.08)),
    ((0.55, 0.79), (0.45, 0.79)),
]


def draw_flowchart(out_path: Path = FIG_DIR / "fig1.png") -> Path:
    n_households, n_msoas = population_counts()

    with plt.rc_context(_PLOT_RC):
        fig, ax = plt.subplots(figsize=(12, 10))

        for text, x, y, w, h, color in build_boxes(n_households, n_msoas):
            ax.add_patch(patches.Rectangle(
                (x, y), w, h, linewidth=1, edgecolor="black", facecolor=color))
            ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                    fontsize=11, fontweight="bold")

        for start, end in _ARROWS:
            ax.annotate("", xy=end, xytext=start,
                        arrowprops=dict(facecolor="black", shrink=0.05,
                                        width=1, headwidth=8))

        ax.set_xlim(0, 1)
        ax.set_ylim(-0.05, 1)
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(out_path, bbox_inches="tight")
        plt.close(fig)

    print(f"Figure 1 written to {out_path} "
          f"({n_households:,} households, {n_msoas:,} MSOAs)")
    return out_path


if __name__ == "__main__":
    draw_flowchart()
