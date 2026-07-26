"""Economic convergent-validity check for the behaviorally-adjusted metric T*.

Correlates the regional mean of the current national INLA T* estimate against
independent regional mean annual household gas expenditure from UK Household
Longitudinal Study (UKHLS) Wave 13. Reproduces the Spearman correlation
reported in the manuscript's "Economic Convergent Validity" section.

Run from the project root:
    python -m src.research.ukhls_convergent_validation
"""
import pandas as pd
import scipy.stats as stats

from src.config.settings import PROCESSED_DIR, RAW_DIR, MSOA_REGION_LOOKUP

UKHLS_HHRESP = (
    RAW_DIR / "ukhls_extracted" / "UKDA-6614-stata"
    / "stata" / "stata14_se" / "ukhls" / "m_hhresp.dta"
)


def _norm(name: str) -> str:
    """Normalise region names so 'Yorkshire and the Humber' aligns across sources."""
    return name.strip().lower()


def load_regional_tstar() -> pd.Series:
    """Current national INLA T*, aggregated to the nine English regions."""
    results = pd.read_csv(PROCESSED_DIR / "msoa_unified_results_inla.csv")
    lookup = pd.read_csv(MSOA_REGION_LOOKUP)
    merged = results.merge(lookup, on="msoa21cd", how="left")
    return merged.groupby("region")["T_star_kwh"].mean()


def load_ukhls_regional_gas_spend() -> pd.Series:
    """UKHLS Wave 13 mean annual gas expenditure by region.

    m_xpgasy: amount spent on gas (annual); m_gor_dv: Government Office Region.
    """
    ukhls = pd.read_stata(
        UKHLS_HHRESP, columns=["m_xpgasy", "m_gor_dv"], convert_categoricals=True
    )
    ukhls["gas_spend"] = pd.to_numeric(ukhls["m_xpgasy"], errors="coerce")
    ukhls = ukhls[ukhls["gas_spend"] > 0]
    return ukhls.groupby(ukhls["m_gor_dv"].astype(str))["gas_spend"].mean()


def correlate_tstar_with_gas_spend(regional_tstar: pd.Series, ukhls_reg: pd.Series) -> pd.DataFrame:
    """Align two region-indexed series by normalized name and pair them up.

    Pure function of its two Series arguments (no I/O), so the alignment logic
    is independently testable without touching disk. Keeps regional_tstar's
    own region-name casing (e.g. "Yorkshire and The Humber") as the result's
    index, since that's the casing used throughout the manuscript.
    """
    gas_by_norm_name = {_norm(name): value for name, value in ukhls_reg.items()}
    aligned_gas = regional_tstar.index.map(lambda region: gas_by_norm_name.get(_norm(region)))
    compare = pd.DataFrame({"T_star": regional_tstar, "gas_spend": aligned_gas}).dropna()
    return compare


def run_ukhls_validation() -> tuple:
    regional_tstar = load_regional_tstar()
    ukhls_reg = load_ukhls_regional_gas_spend()
    compare = correlate_tstar_with_gas_spend(regional_tstar, ukhls_reg)

    rho, p = stats.spearmanr(compare["T_star"], compare["gas_spend"])
    print(compare.sort_values("T_star", ascending=False).to_string())
    print(f"\nSpearman r = {rho:.4f}, p = {p:.4f}, n = {len(compare)}")
    return rho, p, compare


if __name__ == "__main__":
    run_ukhls_validation()
