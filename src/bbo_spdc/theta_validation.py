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
from .validation_metrics import mae, rmse


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
    """Compare paired digitized experimental and paper-numerical ring radii."""

    measured = []
    predicted = []
    units = set()
    for row in rows:
        experimental = row.get("experimental_ring_radius_mm_or_px", float("nan"))
        model = row.get("model_ring_radius_mm_or_px", float("nan"))
        if np.isfinite(experimental) and np.isfinite(model):
            measured.append(float(experimental))
            predicted.append(float(model))
            units.add(row.get("radius_unit", "") or "unspecified")
    if not measured:
        return {
            "points": 0,
            "metric_type": "literature_theta_markers_only",
            "warning": "Karan theta values available, but ring radius values not digitized yet.",
            "rmse": None,
            "mae": None,
            "unit": "",
            "comparison_basis": "",
            "direct_package_model_fit": False,
        }
    unit = units.pop() if len(units) == 1 else "mixed_units"
    return {
        "points": len(measured),
        "metric_type": "digitized_literature_data",
        "warning": "",
        "rmse": rmse(measured, predicted),
        "mae": mae(measured, predicted),
        "unit": unit,
        "comparison_basis": (
            "Karan Figure 8 experimental panels versus corresponding paper numerical panels"
        ),
        "direct_package_model_fit": False,
    }


def _byu_valid_rows(rows: list[dict]) -> list[dict]:
    valid = []
    for row in rows:
        theta = row.get("crystal_angle_face_deg", float("nan"))
        if not np.isfinite(theta):
            theta = row.get("crystal_angle_axis_deg", float("nan"))
        observed = row.get("observed_ring_diameter_no_lens_deg", float("nan"))
        published_model = row.get("model_ring_diameter_deg", float("nan"))
        if np.isfinite(theta) and np.isfinite(observed) and np.isfinite(published_model):
            valid.append(
                {
                    **row,
                    "theta_deg": float(theta),
                    "observed": float(observed),
                    "published_model": float(published_model),
                }
            )
    return sorted(valid, key=lambda row: row["theta_deg"])


def _sample_byu_published_model(
    query_theta_deg: np.ndarray,
    reference_theta_deg: np.ndarray,
    reference_diameter_deg: np.ndarray,
) -> np.ndarray:
    """Interpolate the digitized BYU model curve, with linear edge extension."""

    query = np.asarray(query_theta_deg, dtype=float)
    sampled = np.interp(query, reference_theta_deg, reference_diameter_deg)
    left_slope = (reference_diameter_deg[1] - reference_diameter_deg[0]) / (
        reference_theta_deg[1] - reference_theta_deg[0]
    )
    right_slope = (reference_diameter_deg[-1] - reference_diameter_deg[-2]) / (
        reference_theta_deg[-1] - reference_theta_deg[-2]
    )
    left = query < reference_theta_deg[0]
    right = query > reference_theta_deg[-1]
    sampled[left] = reference_diameter_deg[0] + left_slope * (
        query[left] - reference_theta_deg[0]
    )
    sampled[right] = reference_diameter_deg[-1] + right_slope * (
        query[right] - reference_theta_deg[-1]
    )
    return sampled


def fit_theta_offset(rows: list[dict], fit_offset: bool = True) -> dict:
    """Compare digitized BYU CCD points with its published computational curve."""

    valid = _byu_valid_rows(rows)
    if not valid:
        return {
            "points": 0,
            "available": False,
            "warning": "BYU CSV contains no paired digitized ring-diameter/model values.",
        }
    theta = np.array([row["theta_deg"] for row in valid], dtype=float)
    measured = np.array([row["observed"] for row in valid], dtype=float)
    published_model = np.array([row["published_model"] for row in valid], dtype=float)
    baseline = _sample_byu_published_model(theta, theta, published_model)
    before_rmse = rmse(measured, baseline)
    literature_offset_deg = 0.2
    literature_offset_prediction = _sample_byu_published_model(
        theta + literature_offset_deg, theta, published_model
    )
    best_offset = 0.0
    after = baseline
    if fit_offset:
        candidates = np.linspace(-0.5, 0.5, 1001)
        scores = []
        for offset in candidates:
            prediction = _sample_byu_published_model(theta + offset, theta, published_model)
            scores.append(rmse(measured, prediction))
        best_offset = float(candidates[int(np.argmin(scores))])
        after = _sample_byu_published_model(theta + best_offset, theta, published_model)
    uncertainties = [
        row.get("digitization_uncertainty_deg", float("nan")) for row in valid
    ]
    finite_uncertainties = [value for value in uncertainties if np.isfinite(value)]
    report = {
        "points": len(valid),
        "available": True,
        "metric_type": "digitized_literature_data",
        "comparison_basis": (
            "BYU Figure 3.3 observed CCD data without lens versus published computational curve"
        ),
        "primary_observed_series": "observed_ring_diameter_no_lens_deg",
        "direct_package_model_fit": False,
        "literature_reported_offset_deg": literature_offset_deg,
        "rmse_before_offset_deg": before_rmse,
        "rmse_at_literature_offset_deg": rmse(measured, literature_offset_prediction),
        "rmse_after_offset_deg": rmse(measured, after),
        "mae_after_offset_deg": mae(measured, after),
        "delta_theta_offset_deg": best_offset,
        "fit_offset_enabled": bool(fit_offset),
        "fit_uses_linear_edge_extrapolation": bool(
            np.any(theta + best_offset > theta[-1])
            or np.any(theta + best_offset < theta[0])
        ),
        "digitization_uncertainty_deg": (
            float(np.nanmax(finite_uncertainties)) if finite_uncertainties else None
        ),
    }
    with_lens = np.array(
        [row.get("observed_ring_diameter_with_lens_deg", float("nan")) for row in valid]
    )
    if np.isfinite(with_lens).all():
        report["rmse_after_offset_with_lens_deg"] = rmse(with_lens, after)
        report["mae_after_offset_with_lens_deg"] = mae(with_lens, after)
    return report


def plot_theta_ring_validation(
    config: SPDCConfig,
    karan_rows: list[dict],
    output_path: str | Path,
    theta_min: float = 28.4,
    theta_max: float = 29.4,
    detector_distance_mm: float = 35.0,
) -> dict:
    """Plot package theta model beside any scale-compatible literature digitization."""

    curve = compute_theta_curve(config, theta_min, theta_max, detector_distance_mm)
    report = compare_theta_points(karan_rows)
    has_digitized = report["points"] > 0
    literature_reference_theta_deg = 29.0
    fig, (model_ax, data_ax) = plt.subplots(1, 2, figsize=(12.2, 4.9))
    model_ax.plot(
        curve.theta_deg,
        curve.ring_radius_mm,
        color="#0f766e",
        linewidth=2.3,
        label=f"Sellmeier model ({detector_distance_mm:.0f} mm plane)",
    )
    model_ax.axvline(
        curve.theta_pm_deg,
        color="#111827",
        linestyle="--",
        linewidth=1.2,
        label=f"Calculated theta_PM = {curve.theta_pm_deg:.3f} deg",
    )
    model_ax.axvline(
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
        model_ax.scatter(
            theta_markers,
            np.zeros_like(theta_markers),
            marker="^",
            s=52,
            color="#b45309",
            label="Karan theta locations (context)",
            zorder=4,
        )
    model_ax.set_title("Package model: detector-plane radius")
    model_ax.set_xlabel("BBO optic-axis angle theta_p (deg)")
    model_ax.set_ylabel("Modeled ring radius (mm)")
    model_ax.grid(alpha=0.22)
    model_ax.legend(loc="lower right", fontsize=8)

    if has_digitized:
        digitized = [
            row
            for row in karan_rows
            if np.isfinite(row["experimental_ring_radius_mm_or_px"])
            and np.isfinite(row["model_ring_radius_mm_or_px"])
        ]
        x = np.array([row["theta_p_deg"] for row in digitized])
        y = np.array([row["experimental_ring_radius_mm_or_px"] for row in digitized])
        paper_model = np.array([row["model_ring_radius_mm_or_px"] for row in digitized])
        errors = np.array([row["experimental_ring_radius_uncertainty"] for row in digitized])
        errors = None if not np.isfinite(errors).any() else np.nan_to_num(errors)
        data_ax.errorbar(
            x,
            y,
            yerr=errors,
            fmt="o",
            color="#b91c1c",
            capsize=3,
            label="Experimental panels (digitized)",
        )
        data_ax.plot(
            x,
            paper_model,
            "s-",
            color="#2563eb",
            label="Paper numerical panels (digitized)",
        )
        blob_rows = [
            row
            for row in karan_rows
            if np.isfinite(row["theta_p_deg"])
            and not np.isfinite(row["experimental_ring_radius_mm_or_px"])
        ]
        if blob_rows:
            data_ax.annotate(
                "central blob;\nannular radius undefined",
                xy=(blob_rows[0]["theta_p_deg"], 0),
                xytext=(blob_rows[0]["theta_p_deg"] + 0.035, 6),
                fontsize=8,
                arrowprops={"arrowstyle": "-", "color": "#6b7280"},
            )
        data_ax.text(
            0.04,
            0.95,
            (
                f"RMSE = {report['rmse']:.1f} {report['unit']}\n"
                f"MAE = {report['mae']:.1f} {report['unit']}\n"
                "2 annular points; R² not reported"
            ),
            transform=data_ax.transAxes,
            va="top",
            fontsize=8.5,
            bbox={"facecolor": "white", "edgecolor": "#e5e7eb", "alpha": 0.9},
        )
        title = "Model context and digitized literature comparison: Type-I BBO theta/ring tuning"
    else:
        title = "Theory model with literature theta markers: Type-I BBO theta/ring tuning"
        data_ax.text(
            0.03,
            0.55,
            report["warning"],
            transform=data_ax.transAxes,
            va="center",
            fontsize=9,
            bbox={"facecolor": "white", "edgecolor": "#e5e7eb", "alpha": 0.9},
        )
    data_ax.set_title("Digitized literature data: Karan Fig. 8")
    data_ax.set_xlabel("BBO optic-axis angle theta_p (deg)")
    data_ax.set_ylabel("Ring radial-peak radius (figure px)")
    data_ax.set_xlim(theta_min, theta_max)
    data_ax.set_ylim(bottom=-1)
    data_ax.grid(alpha=0.22)
    if has_digitized:
        data_ax.legend(loc="lower right", fontsize=8)
    fig.suptitle(title, fontsize=12)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
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
    """Generate supplementary BYU paper-internal ring-diameter comparison."""

    report = fit_theta_offset(rows, fit_offset_enabled)
    if not report.get("available"):
        return report
    valid = _byu_valid_rows(rows)
    theta = np.array([row["theta_deg"] for row in valid])
    measured = np.array([row["observed"] for row in valid])
    with_lens = np.array([row["observed_ring_diameter_with_lens_deg"] for row in valid])
    published_model = np.array([row["published_model"] for row in valid])
    corrected_model = _sample_byu_published_model(
        theta + report["delta_theta_offset_deg"], theta, published_model
    )
    uncertainties = np.array(
        [row.get("digitization_uncertainty_deg", float("nan")) for row in valid]
    )
    uncertainties = None if not np.isfinite(uncertainties).any() else np.nan_to_num(uncertainties)
    fig, ax = plt.subplots(figsize=(8.4, 5.1))
    ax.errorbar(
        theta,
        measured,
        yerr=uncertainties,
        fmt="s",
        color="#1d4ed8",
        capsize=2,
        label="CCD observed without lens (digitized)",
    )
    if np.isfinite(with_lens).all():
        ax.scatter(
            theta,
            with_lens,
            facecolors="none",
            edgecolors="#dc2626",
            label="CCD observed with lens (digitized)",
        )
    ax.plot(
        theta,
        published_model,
        color="#059669",
        linewidth=2,
        label="Published computational curve (digitized)",
    )
    if fit_offset_enabled:
        ax.plot(
            theta,
            corrected_model,
            color="#7c3aed",
            linestyle="--",
            linewidth=1.8,
            label="Computational curve sampled after fitted offset",
        )
    ax.set_title("Model vs digitized literature data: supplementary BYU ring diameter")
    ax.set_xlabel("Crystal-face angle (deg; digitized from Figure 3.3)")
    ax.set_ylabel("Ring diameter (deg)")
    metric_text = (
        f"RMSE raw = {report['rmse_before_offset_deg']:.3f} deg\n"
        f"RMSE at reported +0.200 deg = {report['rmse_at_literature_offset_deg']:.3f} deg"
    )
    if fit_offset_enabled:
        metric_text += (
            f"\nFitted offset = {report['delta_theta_offset_deg']:+.3f} deg"
            f"\nRMSE fitted = {report['rmse_after_offset_deg']:.3f} deg"
            f"\nMAE fitted = {report['mae_after_offset_deg']:.3f} deg"
        )
    ax.text(
        0.04,
        0.95,
        metric_text,
        transform=ax.transAxes,
        va="top",
        fontsize=8.5,
        bbox={"facecolor": "white", "edgecolor": "#e5e7eb", "alpha": 0.9},
    )
    ax.grid(alpha=0.22)
    ax.legend(loc="lower right", fontsize=8)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return report
