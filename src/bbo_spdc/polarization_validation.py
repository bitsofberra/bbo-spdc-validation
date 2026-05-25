"""Polarization-entanglement validation against experimental coincidence data."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

_mpl_config_dir = Path(tempfile.gettempdir()) / "bbo_spdc_matplotlib"
_mpl_config_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_config_dir))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .validation_metrics import poisson_sigma, r2_score, rmse, weighted_rmse


EPJ_SOURCE_URL = (
    "https://epjquantumtechnology.springeropen.com/articles/10.1140/epjqt/s40507-024-00298-y"
)
TESTING_REALITY_SOURCE_URL = "https://testing-reality.webflow.io/experiment-4"


def phi_plus_probability(alpha_deg, beta_deg):
    """Balanced |Phi+> linear-polarizer coincidence probability."""

    alpha = np.deg2rad(np.asarray(alpha_deg, dtype=float))
    beta = np.deg2rad(np.asarray(beta_deg, dtype=float))
    return 0.5 * np.cos(alpha - beta) ** 2


def unbalanced_correlated_probability(alpha_deg, beta_deg, p: float, phi_rad: float):
    """Coincidence probability for sqrt(p)|HH> + exp(i phi)sqrt(1-p)|VV>."""

    alpha = np.deg2rad(np.asarray(alpha_deg, dtype=float))
    beta = np.deg2rad(np.asarray(beta_deg, dtype=float))
    amplitude = (
        np.sqrt(p) * np.cos(alpha) * np.cos(beta)
        + np.exp(1j * phi_rad) * np.sqrt(1.0 - p) * np.sin(alpha) * np.sin(beta)
    )
    return np.abs(amplitude) ** 2


def _linear_fit(probability, measured) -> dict:
    design = np.column_stack([np.asarray(probability, dtype=float), np.ones(len(measured))])
    scale, background = np.linalg.lstsq(design, measured, rcond=None)[0]
    predicted = design @ np.array([scale, background])
    return {
        "scale": float(scale),
        "background": float(background),
        "predicted": predicted,
        "r_squared": r2_score(measured, predicted),
        "rmse": rmse(measured, predicted),
    }


def fit_polarization_model(rows: list[dict], dataset_name: str = "") -> tuple[list[dict], dict]:
    """Fit balanced and unbalanced Bell-state models to corrected coincidence counts."""

    if not rows:
        raise ValueError("Polarization validation requires at least one experimental row.")
    alpha = np.array([row["alpha_deg"] for row in rows], dtype=float)
    beta = np.array([row["beta_deg"] for row in rows], dtype=float)
    nc = np.array([row["Nc"] for row in rows], dtype=float)
    nacc = np.nan_to_num(np.array([row.get("Nacc", 0.0) for row in rows], dtype=float))
    corrected = nc - nacc
    normalization = float(np.max(corrected))
    measured = corrected / normalization
    sigma_counts = np.sqrt(poisson_sigma(nc) ** 2 + poisson_sigma(nacc) ** 2)
    sigma = sigma_counts / normalization

    balanced = _linear_fit(phi_plus_probability(alpha, beta), measured)
    best = None
    for p in np.linspace(0.02, 0.98, 97):
        for phi_rad in np.linspace(-np.pi, np.pi, 73):
            fit = _linear_fit(
                unbalanced_correlated_probability(alpha, beta, float(p), float(phi_rad)),
                measured,
            )
            if best is None or fit["r_squared"] > best["r_squared"]:
                best = {**fit, "p": float(p), "phi_rad": float(phi_rad)}
    if best is None:
        raise ValueError("Polarization fit failed.")

    predictions = []
    for index, row in enumerate(rows):
        predictions.append(
            {
                "alpha_deg": row["alpha_deg"],
                "beta_deg": row["beta_deg"],
                "Na": row["Na"],
                "Nb": row["Nb"],
                "Nc": row["Nc"],
                "Nacc": row.get("Nacc", 0.0),
                "Ncorr": float(corrected[index]),
                "sigma_Ncorr": float(sigma_counts[index]),
                "normalized_Ncorr": float(measured[index]),
                "normalized_sigma": float(sigma[index]),
                "balanced_prediction": float(balanced["predicted"][index]),
                "unbalanced_prediction": float(best["predicted"][index]),
            }
        )
    report = {
        "dataset": dataset_name,
        "metric_type": "model_vs_experimental_data",
        "normalization": "Ncorr / max(Ncorr)",
        "correction": "Ncorr = Nc - Nacc",
        "uncertainty": "sigma_Ncorr approximated as sqrt(Nc + Nacc)",
        "points": len(rows),
        "r_squared_balanced": balanced["r_squared"],
        "r_squared_unbalanced": best["r_squared"],
        "rmse_balanced": balanced["rmse"],
        "rmse_unbalanced": best["rmse"],
        "weighted_rmse_unbalanced": weighted_rmse(measured, best["predicted"], sigma),
        "fitted_p": best["p"],
        "fitted_phi_rad": best["phi_rad"],
        "scale": best["scale"],
        "background": best["background"],
    }
    return predictions, report


def write_polarization_predictions(path: str | Path, predictions: list[dict]) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(predictions[0].keys()))
        writer.writeheader()
        writer.writerows(predictions)
    return path


def plot_polarization_validation(
    predictions: list[dict],
    report: dict,
    output_path: str | Path,
    source_label: str,
    source_url: str,
    note: str = "",
) -> Path:
    """Plot normalized experimental coincidences and two Bell-state fits."""

    measured = np.array([row["normalized_Ncorr"] for row in predictions], dtype=float)
    uncertainty = np.array([row["normalized_sigma"] for row in predictions], dtype=float)
    balanced = np.array([row["balanced_prediction"] for row in predictions], dtype=float)
    unbalanced = np.array([row["unbalanced_prediction"] for row in predictions], dtype=float)
    labels = [
        f"{row['alpha_deg']:.1f},{row['beta_deg']:.1f}" for row in predictions
    ]
    index = np.arange(len(predictions))

    if len(predictions) > 40:
        alpha = np.array([row["alpha_deg"] for row in predictions], dtype=float)
        beta = np.array([row["beta_deg"] for row in predictions], dtype=float)
        unique_alpha = np.array(sorted(set(alpha)))
        unique_beta = np.array(sorted(set(beta)))

        def grid(values):
            matrix = np.full((len(unique_alpha), len(unique_beta)), np.nan)
            for a, b, value in zip(alpha, beta, values):
                row_index = int(np.where(unique_alpha == a)[0][0])
                column_index = int(np.where(unique_beta == b)[0][0])
                matrix[row_index, column_index] = value
            return matrix

        extent = [unique_beta.min(), unique_beta.max(), unique_alpha.min(), unique_alpha.max()]
        fig, axes = plt.subplots(2, 2, figsize=(10.8, 8.2))
        panels = [
            (grid(measured), "Experimental normalized coincidences", "viridis"),
            (grid(balanced), "Balanced Phi+ model", "viridis"),
            (grid(unbalanced), "Fitted unbalanced model", "viridis"),
            (grid(measured - unbalanced), "Residual: experiment - fitted model", "coolwarm"),
        ]
        for ax, (matrix, title, cmap) in zip(axes.ravel(), panels):
            image = ax.imshow(matrix, origin="lower", aspect="auto", extent=extent, cmap=cmap)
            ax.set_title(title)
            ax.set_xlabel("Beta / PolB (deg)")
            ax.set_ylabel("Alpha / PolA (deg)")
            fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
        fig.suptitle(f"Model vs experimental data: {source_label} polarization validation")
        fig.text(
            0.02,
            0.02,
            (
                f"R²-based agreement balanced: {100 * report['r_squared_balanced']:.2f}% | "
                f"unbalanced: {100 * report['r_squared_unbalanced']:.2f}% | "
                f"RMSE: {report['rmse_unbalanced']:.4f} | fitted p: {report['fitted_p']:.3f}"
            ),
            fontsize=9,
        )
        if note:
            fig.text(0.02, 0.005, note, fontsize=8, color="#374151")
        fig.text(0.99, 0.005, source_url, fontsize=7.5, ha="right", color="#374151")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.tight_layout(rect=[0.0, 0.06, 1.0, 0.95])
        fig.savefig(output_path, dpi=220)
        plt.close(fig)
        return output_path

    fig, (ax0, ax1) = plt.subplots(
        2, 1, figsize=(10.5, 6.4), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]}
    )
    ax0.errorbar(
        index,
        measured,
        yerr=uncertainty,
        fmt="o",
        color="#111827",
        capsize=2,
        label=f"Experimental: {source_label}",
    )
    ax0.plot(index, balanced, color="#2563eb", linewidth=1.8, label="Balanced Phi+ model")
    ax0.plot(
        index,
        unbalanced,
        color="#b45309",
        linewidth=2.0,
        label="Fitted unbalanced correlated model",
    )
    ax0.set_ylabel("Normalized corrected coincidences")
    ax0.set_title(f"Model vs experimental data: {source_label} polarization validation")
    ax0.text(
        0.99,
        0.95,
        (
            f"R²-based agreement balanced: {100 * report['r_squared_balanced']:.2f}%\n"
            f"R²-based agreement unbalanced: {100 * report['r_squared_unbalanced']:.2f}%\n"
            f"RMSE unbalanced: {report['rmse_unbalanced']:.4f}\n"
            f"fitted p: {report['fitted_p']:.3f}"
        ),
        transform=ax0.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox={"facecolor": "white", "edgecolor": "#e5e7eb", "alpha": 0.92},
    )
    ax0.grid(alpha=0.22)
    ax0.legend(loc="upper left", fontsize=8.5)

    ax1.axhline(0.0, color="#6b7280", linewidth=1.0)
    ax1.bar(index, measured - unbalanced, color="#0f766e")
    ax1.set_ylabel("Residual")
    ax1.set_xlabel("Polarizer setting (alpha, beta) in degrees")
    ax1.set_xticks(index)
    ax1.set_xticklabels(labels, rotation=50, ha="right", fontsize=8)
    ax1.grid(axis="y", alpha=0.22)
    if note:
        fig.text(0.01, 0.01, note, fontsize=8.5, color="#374151")
    fig.text(0.99, 0.01, source_url, fontsize=7.5, ha="right", color="#374151")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0.0, 0.045, 1.0, 1.0])
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return output_path
