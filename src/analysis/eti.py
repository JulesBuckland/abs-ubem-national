import pandas as pd
import numpy as np
import logging
from src.config.settings import (
    PROCESSED_DIR, SYNTHETIC_POP_FILE, HEATING_DEFICIT_FILE,
    ETI_RESULTS_FILE, setup_logging
)

logger = setup_logging("NationalETIGeneration")

def run_national_aggregation():
    logger.info("--- STAGE 4: NATIONAL $T^*$ AGGREGATION & GENERATION ---")
    
    # 1. Load Bayesian Results
    bayes_path = PROCESSED_DIR / "national_bayesian_results.csv"
    if not bayes_path.exists():
        logger.error(f"Bayesian results not found at {bayes_path}. Run Stage 3 first.")
        return
        
    summaries = pd.read_csv(bayes_path)
    summaries['msoa21cd'] = summaries['msoa21cd'].astype(str).str.strip().str.upper()
    logger.info(f"Loaded posterior summaries for {len(summaries)} MSOAs.")
    
    # 2. Load Synthetic Population and Heating Deficits
    logger.info("Loading synthetic population and heating deficits...")
    pop_path = PROCESSED_DIR / SYNTHETIC_POP_FILE
    deficit_path = PROCESSED_DIR / HEATING_DEFICIT_FILE
    
    if not pop_path.exists():
        logger.error(f"Synthetic population not found at {pop_path}")
        return
        
    if not deficit_path.exists():
        logger.error("Heating deficits not found.")
        return
        
    pop = pd.read_parquet(pop_path)
    pop['msoa21cd'] = pop['msoa21cd'].astype(str).str.strip().str.upper()

    deficits = pd.read_csv(deficit_path)
    deficits['msoa21cd'] = deficits['msoa21cd'].astype(str).str.strip().str.upper()
    
    # 3. Join everything
    # Merge posterior summaries with synthetic population
    df = pop.merge(summaries, on='msoa21cd', how='inner')
    
    # Merge with original confounders for income_dep_score
    conf_path = PROCESSED_DIR / "msoa_confounders_national.csv"
    conf = pd.read_csv(conf_path)
    conf['msoa_cd'] = conf['msoa_cd'].astype(str).str.strip().str.upper()
    df = df.merge(conf[['msoa_cd', 'income_dep_score']], left_on='msoa21cd', right_on='msoa_cd')
    
    logger.info("Computing Empirical Thermal Index ($T^*$) for all households...")
    
    # Formula: $T^*$ isolates structural underperformance from house-size and income effects
    # Standardise income using the saved national scaling parameters
    income_z = (df['income_dep_score'] - df['income_mean']) / df['income_std']

    # Compute rationing-adjusted residual
    log_rationing_component = df['beta_income_mean'] * income_z + df['msoa_effect_mean']

    # $T^*$ in kWh/year
    df['empirical_thermal_index'] = np.exp(
        np.log(df['empirical_gas_kwh']) - log_rationing_component
    )
    
    # 4. Final Aggregation to MSOA level
    msoa_eti = df.groupby('msoa21cd').agg({
        'empirical_thermal_index': 'mean',
        'empirical_gas_kwh': 'mean',
        'theoretical_gas_kwh': 'mean',
        'beta_income_mean': 'mean'
    }).reset_index()
    
    # Merge with rationing stats
    msoa_eti = msoa_eti.merge(deficits[['msoa21cd', 'prop_rationing', 'heating_deficit']], on='msoa21cd')
    
    # 5. Save results
    output_path = PROCESSED_DIR / ETI_RESULTS_FILE
    msoa_eti.to_csv(output_path, index=False)
    logger.info(f"National $T^*$ results saved to {output_path}")
    logger.info(f"Final MSOA count: {len(msoa_eti)} (England)")

if __name__ == "__main__":
    run_national_aggregation()
