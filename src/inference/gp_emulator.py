"""
10c_gp_emulator.py
==================
Trains a Gaussian Process emulator on the LHS-sampled EnergyPlus results.
The emulator predicts annual thermal energy demand T_h (kWh/year) given:
    [floor_area, wall_u, ach, wwr, form_code]

Acceptance criterion: held-out R² > 0.99 on 50 test points per archetype.

Outputs:
  - data/processed/gp_emulator.pkl  (GP model + scaler, ready for joblib.load)
  - data/processed/gp_validation_stats.json
  - outputs/figures/gp_validation.png

Usage:
  python src/inference/gp_emulator.py              # train and save
  python src/inference/gp_emulator.py --validate   # load saved model, print R²
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json
import joblib
import argparse
import logging
from pathlib import Path
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, WhiteKernel, ConstantKernel
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("GPEmulator")

from src.config import settings as config

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR      = config.BASE_DIR
PHYSICS_DIR   = config.RAW_DIR / "physics"
PROCESSED_DIR = config.PROCESSED_DIR
FIGURES_DIR   = config.BASE_DIR / "outputs" / "figures"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

COMBINED_CSV   = PHYSICS_DIR / "lhs_results_combined.csv"
MODEL_PATH     = PROCESSED_DIR / "gp_emulator.pkl"
STATS_PATH     = PROCESSED_DIR / "gp_validation_stats.json"
FIGURE_PATH    = FIGURES_DIR  / "gp_validation.png"

FEATURES       = ["floor_area", "wall_u", "ach", "wwr", "form_code", "hdd"]
TARGET         = "T_h"
RANDOM_SEED    = 42
TEST_FRACTION  = 50 / 300   # 50 held-out per archetype


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    if not COMBINED_CSV.exists():
        raise FileNotFoundError(
            f"Combined LHS results not found at {COMBINED_CSV}.\n"
            "Run 00a_lhs_sampler.py then 00b_energyplus_lhs_batch.py first."
        )
    df = pd.read_csv(COMBINED_CSV)
    before = len(df)
    df = df[df["status"] == "ok"].dropna(subset=FEATURES + [TARGET])
    df = df[df[TARGET] > 0]
    logger.info(f"Loaded {len(df)} valid rows (dropped {before - len(df)} failed/missing).")
    return df


def train_gp(df: pd.DataFrame):
    X = df[FEATURES].values.astype(float)
    y = df[TARGET].values.astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_FRACTION, random_state=RANDOM_SEED
    )
    
    # Subsample training data to prevent OOM errors on 8000^2 covariance matrix
    MAX_TRAIN_POINTS = 500
    if len(X_train) > MAX_TRAIN_POINTS:
        logger.info(f"Subsampling training set from {len(X_train)} to {MAX_TRAIN_POINTS} to prevent RAM crash.")
        X_train, _, y_train, _ = train_test_split(
            X_train, y_train, train_size=MAX_TRAIN_POINTS, random_state=RANDOM_SEED
        )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    # Matérn(ν=2.5) kernel: once-differentiable, standard for physical emulators
    # WhiteKernel absorbs observation noise (numerical/EnergyPlus discretisation)
    kernel = (
        ConstantKernel(1.0, constant_value_bounds=(1e-3, 1e3))
        * Matern(length_scale=np.ones(len(FEATURES)), length_scale_bounds=(1e-2, 1e3), nu=2.5)
        + WhiteKernel(noise_level=1e-5, noise_level_bounds=(1e-10, 1e-1))
    )

    gp = GaussianProcessRegressor(
        kernel=kernel,
        n_restarts_optimizer=0,
        normalize_y=True,
        random_state=RANDOM_SEED,
    )

    logger.info(f"Training GP on {len(X_train)} points with {len(FEATURES)} features...")
    gp.fit(X_train_s, y_train)
    logger.info(f"Optimised kernel: {gp.kernel_}")

    # Validation
    y_pred, y_std = gp.predict(X_test_s, return_std=True)
    r2   = r2_score(y_test, y_pred)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))

    logger.info(f"Test R²   = {r2:.4f}  (target ≥ 0.99)")
    logger.info(f"Test MAE  = {mae:.1f} kWh/year")
    logger.info(f"Test RMSE = {rmse:.1f} kWh/year")

    if r2 < 0.99:
        logger.warning(
            f"R² = {r2:.4f} < 0.99 — emulator does not meet acceptance threshold.\n"
            "Options: increase N_SAMPLES in 10a_lhs_sampler.py, or check EnergyPlus run quality."
        )
    else:
        logger.info("✓ Acceptance criterion met (R² ≥ 0.99).")

    # Save stats
    stats = {
        "r2": float(r2),
        "mae_kwh_year": float(mae),
        "rmse_kwh_year": float(rmse),
        "n_train": int(len(X_train)),
        "n_test":  int(len(X_test)),
        "kernel":  str(gp.kernel_),
        "acceptance_met": bool(r2 >= 0.99),
    }
    with open(STATS_PATH, "w") as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Stats saved → {STATS_PATH}")

    return gp, scaler, X_test, y_test, y_pred, y_std, stats


def plot_validation(y_test, y_pred, y_std, r2):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # --- Panel 1: predicted vs actual ---
    ax = axes[0]
    vmin = min(y_test.min(), y_pred.min())
    vmax = max(y_test.max(), y_pred.max())
    ax.scatter(y_test, y_pred, alpha=0.4, s=12, color="#2563EB", label="EnergyPlus runs")
    ax.plot([vmin, vmax], [vmin, vmax], "r--", lw=1.5, label="1:1 line")
    ax.fill_between(
        np.sort(y_test),
        np.sort(y_pred) - 2 * y_std[np.argsort(y_test)],
        np.sort(y_pred) + 2 * y_std[np.argsort(y_test)],
        alpha=0.12, color="#2563EB", label="GP 2σ band"
    )
    ax.set_xlabel("EnergyPlus T_h  (kWh/year)", fontsize=11)
    ax.set_ylabel("GP Predicted T_h  (kWh/year)", fontsize=11)
    ax.set_title(f"GP Emulator Validation  (R² = {r2:.4f})", fontsize=12)
    ax.legend(fontsize=9)

    # --- Panel 2: residuals ---
    ax2 = axes[1]
    residuals = y_pred - y_test
    ax2.hist(residuals, bins=40, color="#16A34A", edgecolor="white", alpha=0.8)
    ax2.axvline(0, color="black", lw=1.2, linestyle="--")
    ax2.set_xlabel("Residual  (kWh/year)", fontsize=11)
    ax2.set_ylabel("Count", fontsize=11)
    ax2.set_title("Prediction Residuals", fontsize=12)
    ax2.text(0.97, 0.95,
             f"Mean: {residuals.mean():.1f}\nSD: {residuals.std():.1f}",
             transform=ax2.transAxes, ha="right", va="top",
             fontsize=9, bbox=dict(boxstyle="round", fc="white", alpha=0.7))

    plt.tight_layout()
    plt.savefig(FIGURE_PATH, dpi=150, bbox_inches="tight")
    logger.info(f"Validation plot → {FIGURE_PATH}")
    plt.close()


def save_model(gp, scaler):
    joblib.dump({"gp": gp, "scaler": scaler, "features": FEATURES}, MODEL_PATH)
    logger.info(f"Model saved → {MODEL_PATH}")


# ---------------------------------------------------------------------------
# Validation-only mode
# ---------------------------------------------------------------------------
def validate_saved():
    if not MODEL_PATH.exists():
        logger.error(f"No saved model at {MODEL_PATH}. Train first.")
        return
    payload = joblib.load(MODEL_PATH)
    gp, scaler = payload["gp"], payload["scaler"]

    df = load_data()
    X = df[FEATURES].values.astype(float)
    y = df[TARGET].values.astype(float)
    X_s = scaler.transform(X)
    y_pred, _ = gp.predict(X_s, return_std=True)
    r2 = r2_score(y, y_pred)
    logger.info(f"Full-sample R² (saved model) = {r2:.4f}")

    if STATS_PATH.exists():
        with open(STATS_PATH) as f:
            stats = json.load(f)
        logger.info(f"Held-out test R² (from training): {stats['r2']:.4f}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main(validate: bool = False):
    if validate:
        validate_saved()
        return

    df = load_data()
    gp, scaler, X_test, y_test, y_pred, y_std, stats = train_gp(df)
    save_model(gp, scaler)
    plot_validation(y_test, y_pred, y_std, stats["r2"])
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true",
                        help="Load the saved emulator and report R² without retraining.")
    args = parser.parse_args()
    main(validate=args.validate)
