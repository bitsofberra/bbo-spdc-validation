"""Theta tuning and non-collinear ring validation utilities."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

_mpl_config_dir = Path(tempfile.gettempdir()) / "bbo_spdc_matplotlib"
_mpl_config_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_mpl_config_dir))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .phase_matching import (
    SPDCConfig,
    external_angle_deg,
    find_internal_emission_angle_deg,
    find_type1_phase_matching_angle_deg,
)
from .validation_metrics import mae, r2_score, rmse


KARAN_SOURCE_URL = "https://arxiv.org/abs/1810.01184"
BYU_SOURCE_URL = "https://physics.byu.edu/docs/thesis/103"


@dataclass(frozen=True)
class ThetaCurve:
    theta_deg: np.ndarray
    external_angle_deg: np.ndarray
    ring_radius_mm: np.ndarray
    detector_distance_mm: float
    theta_pm_deg: float


def _external_angle_or_zero(config: SPDCConfig, theta_deg: float) -> float:
    tuned = config.with_theta(float(theta_deg))
    internal = find_internal_emission_angle_deg(tuned)
    external = external_angle_deg(tuned, internal)
    return 0.0 if not np.isfinite(external) else float(external)


def compute_theta_curve(
    config: SPDCConfig,
    theta_min: float = 28.4,
    theta_max: float = 29.4,
    detector_distance_mm: float = 100.0,
    points: int = 301,
) -> ThetaCurve:
    """Calculate model-predicted Type-I ring radius while tuning BBO theta."""

    theta = np.linspace(theta_min, theta_max, points)
    angle = np.array([_external_angle_or_zero(config, value) for value in theta])
    radius = detector_distance_mm * np.tan(np.deg2rad(angle))
    return ThetaCurve(
        theta_deg=theta,
        external_angle_deg=angle,
        ring_radius_mm=radius,
        detector_distance_mm=float(detector_distance_mm),
        theta_pm_deg=find_type1_phase_matching_angle_deg(config),
    )


def compare_theta_points(rows: list[dict]) -> dict:
    """Compare paired digitized literature and model ring radii, when present."""

    measured = []
    predicted = []
    for row in rows:
        experimental = row.get("experimental_ring_radius_mm_or_px", float("nan"))
        model = row.get("model_ring_radius_mm_or_px", float("nan"))
        if np.isfinite(experimental) and np.isfinite(model):
            measured.append(float(experimental))
            predicted.append(float(model))
    if not measured:
        return {
            "points": 0,
            "metric_type": "literature_theta_markers_only",
            "warning": "Karan theta values available, but ring radius values not digitized yet.",
            "rmse": None,
            "mae": None,
        }
    return {
        "points": len(measured),
        "metric_type": "digitized_literature_data",
        "warning": "",
        "rmse": rmse(measured, predicted),
        "mae": mae(measured, predicted),
    }


def _byu_valid_rows(rows: list[dict]) -> list[dict]:
    valid = []
    for row in rows:
        theta = row.get("crystal_angle_axis_deg", float("nan"))
        if not np.isfinite(theta):
            theta = row.get("crystal_angle_face_deg", float("nan"))
        observed = row.get("observed_ring_diameter_no_lens_deg", float("nan"))
        if np.isfinite(theta) and np.isfinite(observed):
            valid.append({**row, "theta_deg": float(theta), "observed": float(observed)})
    return valid


def _byu_model_diameter(row: dict, theta_offset_deg: float = 0.0) -> float:
    config = SPDCConfig(
        pump_wavelength_m=float(row["pump_nm"]) * 1e-9,
        signal_wavelength_m=float(row["daughter_nm"]) * 1e-9,
        idler_wavelength_m=float(row["daughter_nm"]) * 1e-9,
        theta_deg=float(row["theta_deg"]) + theta_offset_deg,
    )
    return 2.0 * _external_angle_or_zero(config, config.theta_deg)


def fit_theta_offset(rows: list[dict], fit_offset: bool = True) -> dict:
    """Evaluate supplementary BYU ring diameter data and optional theta offset."""

    valid = _byu_valid_rows(rows)
    if not valid:
        return {
            "points": 0,
            "available": False,
            "warning": "BYU CSV template contains no digitized ring diameter values.",
        }
    measured = np.array([row["observed"] for row in valid], dtype=float)
    baseline = np.array([_byu_model_diameter(row) for row in valid])
    before_rmse = rmse(measured, baseline)
    best_offset = 0.0
    after = baseline
    if fit_offset:
        candidates = np.linspace(-0.5, 0.5, 1001)
        scores = []
        for offset in candidates:
            prediction = np.array([_byu_model_diameter(row, offset) for row in valid])
            scores.append(rmse(measured, prediction))
        best_offset = float(candidates[int(np.argmin(scores))])
        after = np.array([_byu_model_diameter(row, best_offset) for row in valid])
    report = {
        "points": len(valid),
        "available": True,
        "rmse_before_offset_deg": before_rmse,
        "rmse_after_offset_deg": rmse(measured, after),
        "mae_after_offset_deg": mae(measured, after),
        "delta_theta_offset_deg": best_offset,
    }
    if len(valid) >= 8:
        report["r_squared_after_offset"] = r2_score(measured, after)
    return report


def plot_theta_ring_validation(
    config: SPDCConfig,
    karan_rows: list[dict],
    output_path: str | Path,
    theta_min: float = 28.4,
    theta_max: float = 29.4,
    detector_distance_mm: float = 100.0,
) -> dict:
    """Plot theta tuning curve with measured/digitized literature overlays when available."""

    curve = compute_theta_curve(config, theta_min, theta_max, detector_distance_mm)
    report = compare_theta_points(karan_rows)
    has_digitized = report["points"] > 0
    literature_reference_theta_deg = 29.0
    fig, ax = plt.subplots(figsize=(8.2, 4.9))
    ax.plot(
        curve.theta_deg,
        curve.ring_radius_mm,
        color="#0f766e",
        linewidth=2.3,
        label=f"Sellmeier model ({detector_distance_mm:.0f} mm plane)",
    )
    ax.axvline(
        curve.theta_pm_deg,
        color="#111827",
        linestyle="--",
        linewidth=1.2,
        label=f"Calculated theta_PM = {curve.theta_pm_deg:.3f} deg",
    )
    ax.axvline(
        literature_reference_theta_deg,
        color="#7c3aed",
        linestyle=":",
        linewidth=1.3,
        label="Literature reference approx. 29.0 deg",
    )
    theta_markers = np.array(
        [row["theta_p_deg"] for row in karan_rows if np.isfinite(row["theta_p_deg"])],
        dtype=float,
    )
    if theta_markers.size:
        ax.scatter(
            theta_markers,
            np.zeros_like(theta_markers),
            marker="^",
            s=52,
            color="#b45309",
            label="Karan et al. theta values only (no digitized radius)",
            zorder=4,
        )
    if has_digitized:
        digitized = [
            row
            for row in karan_rows
            if np.isfinite(row["experimental_ring_radius_mm_or_px"])
            and np.isfinite(row["model_ring_radius_mm_or_px"])
        ]
        x = np.array([row["theta_p_deg"] for row in digitized])
        y = np.array([row["experimental_ring_radius_mm_or_px"] for row in digitized])
        errors = np.array([row["experimental_ring_radius_uncertainty"] for row in digitized])
        errors = None if not np.isfinite(errors).any() else np.nan_to_num(errors)
        ax.errorbar(
            x,
            y,
            yerr=errors,
            fmt="o",
            color="#b91c1c",
            capsize=3,
            label="Digitized literature data",
        )
        title = "Model vs digitized literature data: Type-I BBO theta/ring tuning"
    else:
        title = "Theory model with literature theta markers: Type-I BBO theta/ring tuning"
        ax.text(
            0.03,
            0.94,
            report["warning"],
            transform=ax.transAxes,
            va="top",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "#e5e7eb", "alpha": 0.9},
        )
    ax.set_title(title)
    ax.set_xlabel("BBO optic-axis angle theta_p (deg)")
    ax.set_ylabel("Model ring radius at detector plane (mm)")
    ax.grid(alpha=0.22)
    ax.legend(loc="lower right", fontsize=8.5)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return {
        **report,
        "theta_pm_deg": curve.theta_pm_deg,
        "literature_reference_theta_deg": literature_reference_theta_deg,
        "source_url": KARAN_SOURCE_URL,
    }


def plot_byu_ring_diameter_validation(
    rows: list[dict],
    output_path: str | Path,
    fit_offset_enabled: bool = False,
) -> dict:
    """Generate supplementary BYU comparison only when digitized values exist."""

    report = fit_theta_offset(rows, fit_offset_enabled)
    if not report.get("available"):
        return report
    valid = _byu_valid_rows(rows)
    theta = np.array([row["theta_deg"] for row in valid])
    measured = np.array([row["observed"] for row in valid])
    model = np.array(
        [_byu_model_diameter(row, report["delta_theta_offset_deg"]) for row in valid]
    )
    order = np.argsort(theta)
    fig, ax = plt.subplots(figsize=(7.4, 4.5))
    ax.scatter(theta, measured, color="#111827", label="Digitized BYU data")
    ax.plot(theta[order], model[order], color="#0f766e", label="Model with theta offset")
    ax.set_title("Model vs digitized literature data: supplementary BYU ring diameter")
    ax.set_xlabel("Crystal-axis angle (deg)")
    ax.set_ylabel("Ring diameter (deg)")
    ax.text(
        0.04,
        0.95,
        (
            f"RMSE before: {report['rmse_before_offset_deg']:.3g} deg\n"
            f"RMSE after: {report['rmse_after_offset_deg']:.3g} deg\n"
            f"offset: {report['delta_theta_offset_deg']:.3g} deg"
        ),
        transform=ax.transAxes,
        va="top",
    )
    ax.grid(alpha=0.22)
    ax.legend()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return report
