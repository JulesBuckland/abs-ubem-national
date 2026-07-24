import arviz as az
import pymc as pm
import pandas as pd
from pathlib import Path
from src.config.settings import PROCESSED_DIR, setup_logging
import logging
import matplotlib.pyplot as plt

logger = setup_logging("PublicationBayesian")
FIG_DIR = Path("manuscript/figures")
FIG_DIR.mkdir(exist_ok=True, parents=True)

# Gelman/ArviZ Publication Styling
az.style.use("arviz-darkgrid")
plt.rcParams.update({
    'font.size': 14,
    'axes.titlesize': 16,
    'figure.dpi': 300,
    'savefig.dpi': 300
})

def generate_bayesian_diagnostics():
    logger.info("Generating Gelman-compliant Bayesian Diagnostic Plots...")
    try:
        # Load the inference data
        trace_path = PROCESSED_DIR / "national_trace.nc"
        if not trace_path.exists():
            logger.warning(f"Trace file not found at {trace_path}. Run inference first.")
            return

        idata = az.from_netcdf(str(trace_path))
        
        # 1. Rank Trace Plots (GELMAN RULE: Avoid standard traces, use rank-normalized)
        logger.info("Generating Rank Trace Plot...")
        # We plot a subset of variables to avoid massive unreadable plots
        vars_to_plot = [v for v in idata.posterior.data_vars if "msoa" not in v and "edge" not in v]
        
        axes = az.plot_trace(idata, var_names=vars_to_plot, kind="rank_vlines")
        fig = axes[0, 0].figure
        fig.suptitle("Rank-Normalized Trace Plots (Convergence Diagnostic)", fontsize=18)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.savefig(FIG_DIR / "bayesian_rank_trace.png")
        plt.close(fig)

        # 2. Forest Plot (GELMAN RULE: Use for varying effects/uncertainty hierarchy)
        logger.info("Generating Forest Plot...")
        axes = az.plot_forest(idata, var_names=vars_to_plot, combined=True, hdi_prob=0.95)
        fig = axes[0].figure
        fig.suptitle("Posterior Parameter Estimates (95% HDI)", fontsize=18)
        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        fig.savefig(FIG_DIR / "bayesian_forest_plot.png")
        plt.close(fig)

        # 3. LOO-PIT Calibration (GELMAN RULE: Evaluate conditional predictive calibration)
        if "posterior_predictive" in idata.groups():
            logger.info("Generating LOO-PIT Plot for Model Calibration...")
            ax = az.plot_loo_pit(idata, y="obs")
            fig = ax.figure
            fig.suptitle("LOO-PIT Calibration (Uniform = Well Calibrated)", fontsize=18)
            fig.tight_layout()
            fig.savefig(FIG_DIR / "bayesian_loo_pit.png")
            plt.close(fig)
            
            # 4. Posterior Predictive Check (Density)
            logger.info("Generating PPC Density Plot...")
            ax = az.plot_ppc(idata, num_pp_samples=100)
            fig = ax.figure
            fig.suptitle("Posterior Predictive Check (Simulations vs Observed)", fontsize=18)
            fig.tight_layout()
            fig.savefig(FIG_DIR / "bayesian_ppc_density.png")
            plt.close(fig)
        else:
            logger.warning("No posterior_predictive group found in inference data. Skipping PPCs.")
            
    except Exception as e:
        logger.error(f"Failed generating Bayesian diagnostics: {e}")

if __name__ == "__main__":
    generate_bayesian_diagnostics()
