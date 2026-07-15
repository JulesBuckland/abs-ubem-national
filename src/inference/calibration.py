import pandas as pd
import numpy as np
import pymc as pm
import arviz as az
from src.config.settings import PROCESSED_DIR, RANDOM_SEED
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("BayesianCalibration")

def run_calibration():
    logger.info("--- STAGE 2: JOINT HIERARCHICAL CALIBRATION ---")
    
    gas = pd.read_csv(PROCESSED_DIR / "gm_gas_2022.csv")
    mix = pd.read_csv(PROCESSED_DIR / "lsoa_archetype_mix.csv")
    imd = pd.read_csv(PROCESSED_DIR / "lsoa_imd_gm.csv")
    priors_raw = pd.read_csv(PROCESSED_DIR / "gm_archetype_priors.csv").set_index('Archetype')
    census = pd.read_csv(PROCESSED_DIR / "gm_building_stock_census.csv")

    # Align spatial datasets
    common = sorted(list(set(gas['lsoa_cd']) & set(mix['LSOA21CD']) & set(imd['lsoa_cd']) & set(census['lsoa_cd'])))
    gas = gas[gas['lsoa_cd'].isin(common)].sort_values('lsoa_cd')
    mix = mix[mix['LSOA21CD'].isin(common)].sort_values('LSOA21CD')
    imd = imd[imd['lsoa_cd'].isin(common)].sort_values('lsoa_cd')
    census = census[census['lsoa_cd'].isin(common)].sort_values('lsoa_cd')

    available_archetypes = [a for a in mix.columns if a in priors_raw.index]
    
    # Model Inputs
    X = (census.iloc[:, 1].values.reshape(-1, 1) * 
         (mix[available_archetypes].values / 100.0) * 
         priors_raw.loc[available_archetypes, 'Mean_Area'].values.reshape(1, -1)) / 1e6
    y_obs = gas['annual_gas_kwh'].values / 1e6
    income_scores = imd['income_score'].values

    # Priors
    prior_means = np.array([200.0] * len(available_archetypes)) # Generalized fallback

    with pm.Model() as model:
        # Building Intensities
        intensities = pm.TruncatedNormal("intensities", mu=prior_means, sigma=50.0, lower=20.0, shape=len(available_archetypes))
        # Behavioral Rationing (Global)
        beta_dep = pm.Normal("beta_dep", mu=1.0, sigma=0.5)
        # Sigmoid Multiplier [0.5, 1.0]
        b_mult = 0.5 + 0.5 * pm.math.sigmoid(-beta_dep * income_scores)
        
        # Likelihood
        mu = pm.math.dot(X, intensities) * b_mult
        sigma = pm.HalfNormal("sigma", sigma=1.0)
        pm.Normal("y", mu=mu, sigma=sigma, observed=y_obs)
        
        trace = pm.sample(1000, tune=500, target_accept=0.95, chains=4, random_seed=RANDOM_SEED)
        az.to_netcdf(trace, str(PROCESSED_DIR / "calibration_trace.nc"))
        
    logger.info("Calibration Complete. Trace saved.")

if __name__ == "__main__":
    run_calibration()
