"""Economic convergent-validity check for the behaviorally-adjusted metric T*.

Correlates the regional mean of the current national INLA T* estimate against
independent regional mean annual household gas expenditure from UK Household
Longitudinal Study (UKHLS) Wave 13. Reproduces the Spearman correlation
reported in the manuscript's "Economic Convergent Validity" section.

Run from the project root:
    python -m src.research.ukhls_convergent_validation
"""
from pathlib import Path

import pandas as pd
import scipy.stats as stats

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
INLA_RESULTS = PROCESSED / "msoa_unified_results_inla.csv"
REGION_LOOKUP = PROCESSED / "msoa_region_lookup.csv"
UKHLS_HHRESP = (
    PROJECT_ROOT
    / "data" / "raw" / "ukhls_extracted"
    / "UKDA-6614-stata" / "stata" / "stata14_se" / "ukhls" / "m_hhresp.dta"
)


def _norm(name: str) -> str:
    """Normalise region names so 'Yorkshire and the Humber' aligns across sources."""
    return name.strip().lower()


def run_ukhls_validation() -> tuple:
    # 1. Current national INLA T*, aggregated to the nine English regions.
    results = pd.read_csv(INLA_RESULTS)
    lookup = pd.read_csv(REGION_LOOKUP)
    merged = results.merge(lookup, on="msoa21cd", how="left")
    regional_tstar = merged.groupby("region")["T_star_kwh"].mean()

    # 2. UKHLS Wave 13 mean annual gas expenditure by region.
    #    m_xpgasy: amount spent on gas (annual); m_gor_dv: Government Office Region.
    ukhls = pd.read_stata(
        UKHLS_HHRESP, columns=["m_xpgasy", "m_gor_dv"], convert_categoricals=True
    )
    ukhls["gas_spend"] = pd.to_numeric(ukhls["m_xpgasy"], errors="coerce")
    ukhls = ukhls[ukhls["gas_spend"] > 0]
    ukhls_reg = ukhls.groupby(ukhls["m_gor_dv"].astype(str))["gas_spend"].mean()

    # 3. Align on the common English regions and correlate.
    uk_idx = {_norm(r): r for r in ukhls_reg.index}
    mo_idx = {_norm(r): r for r in regional_tstar.index}
    common = sorted(set(uk_idx) & set(mo_idx))
    compare = pd.DataFrame(
        {
            "T_star": [regional_tstar[mo_idx[k]] for k in common],
            "gas_spend": [ukhls_reg[uk_idx[k]] for k in common],
        },
        index=[mo_idx[k] for k in common],
    )

    rho, p = stats.spearmanr(compare["T_star"], compare["gas_spend"])
    print(compare.sort_values("T_star", ascending=False).to_string())
    print(f"\nSpearman r = {rho:.4f}, p = {p:.4f}, n = {len(compare)}")
    return rho, p, compare


if __name__ == "__main__":
    run_ukhls_validation()
