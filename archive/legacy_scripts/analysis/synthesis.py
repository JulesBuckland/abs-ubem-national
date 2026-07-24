import pandas as pd
import numpy as np
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("VisionarySynthesis")

PROCESSED_DIR = Path("data/processed")

def standardize(series):
    return (series - series.mean()) / series.std()

def run_visionary_synthesis():
    logger.info("Starting Visionary Synthesis: The Entropic Equity Framework")
    
    # 1. Load Data
    eti_df = pd.read_csv(PROCESSED_DIR / "empirical_thermal_index_results.csv")
    conf_df = pd.read_csv(PROCESSED_DIR / "msoa_confounders_national.csv")
    
    # Merge on MSOA code
    # Note: eti_df uses 'msoa21cd', conf_df uses 'msoa_cd'
    df = eti_df.merge(conf_df, left_on='msoa21cd', right_on='msoa_cd')
    
    # 2. Standardize Metrics
    df['z_eti'] = standardize(df['empirical_thermal_index'])
    df['z_imd'] = standardize(df['income_dep_score'])
    df['z_overcrowd'] = standardize(df['overcrowding_prev'])
    
    # 3. Synthesize "Epistemic Entropy" (Uncertainty Signal)
    # Lateral Thinking: Uncertainty is highest where the "Age-Built-Form Paradox" is deepest.
    # We use a non-linear interaction of deprivation and physical requirement as a proxy for posterior variance.
    df['epistemic_entropy'] = np.sqrt(np.abs(df['z_eti'] * df['z_imd'])) + 0.1 * np.random.normal(0, 1, len(df))
    df['epistemic_entropy'] = np.clip(df['epistemic_entropy'], 0.1, 5.0)
    
    # 4. Calculate the Thermodynamic Regret Index (S_visionary)
    # The exponential interaction ensures we target the "Singularity" of the Age-Built-Form Paradox.
    # Overcrowding acts as a "Metabolic Buffer" in the denominator.
    numerator = df['z_eti'] * df['z_imd']
    denominator = 1.0 + np.abs(df['z_overcrowd'])
    
    df['visionary_priority_score'] = np.exp(numerator / denominator) * df['epistemic_entropy']
    
    # 5. Rank and Compare
    df['visionary_rank'] = df['visionary_priority_score'].rank(ascending=False)
    
    # Traditional linear rank (for comparison) - w1=0.6, w2=0.4
    df['linear_priority_score'] = 0.6 * df['z_eti'] + 0.4 * df['z_imd']
    df['linear_rank'] = df['linear_priority_score'].rank(ascending=False)
    
    # 6. Save Outputs
    output_path = PROCESSED_DIR / "visionary_equity_results.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Visionary results saved to {output_path}")
    
    # 7. Print Top 10 Visionary vs Linear
    print("\n--- TOP 10 VISIONARY PRIORITY MSOAs (ENTROPIC EQUITY) ---")
    print(df.sort_values('visionary_rank').head(10)[['msoa21cd', 'visionary_priority_score', 'z_eti', 'z_imd', 'epistemic_entropy']])
    
    print("\n--- TOP 10 TRADITIONAL LINEAR MSOAs ---")
    print(df.sort_values('linear_rank').head(10)[['msoa21cd', 'linear_priority_score', 'z_eti', 'z_imd']])

if __name__ == "__main__":
    run_visionary_synthesis()
