"""Qualitative spatial validation and ring-shape characterization."""

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

from .phase_matching import SPDCConfig
from .ring import normalize_image, simulate_spdc_ring_image


GLASGOW_SOURCE_URL = "https://researchdata.gla.ac.uk/1269/"
JOSA_B_SOURCE_URL = "https://opg.optica.org/josab/abstract.cfm?uri=josab-32-10-2096"


def subtract_background(matrix: np.ndarray, percentile: float = 10.0) -> np.ndarray:
    """Remove a robust low-percentile background and clip negative intensities."""

    values = np.asarray(matrix, dtype=float)
    background = float(np.nanpercentile(values, percentile))
    return np.clip(np.nan_to_num(values - background), 0.0, None)


def estimate_center(matrix: np.ndarray) -> tuple[float, float]:
    """Estimate image center of mass in pixel coordinates."""

    weights = subtract_background(matrix)
    total = float(np.sum(weights))
    if total <= 0:
        return (0.5 * (matrix.shape[1] - 1), 0.5 * (matrix.shape[0] - 1))
    y, x = np.indices(weights.shape)
    return (float(np.sum(x * weights) / total), float(np.sum(y * weights) / total))


def radial_profile(
    matrix: np.ndarray,
    center: tuple[float, float] | None = None,
    bins: int | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Return radial-average intensity around the fitted center, in pixels."""

    image = subtract_background(matrix)
    center_x, center_y = center or estimate_center(image)
    y, x = np.indices(image.shape)
    radius = np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
    maximum_radius = float(min(image.shape) / 2.0)
    bins = bins or max(12, int(maximum_radius))
    edges = np.linspace(0.0, maximum_radius, bins + 1)
    centers = 0.5 * (edges[:-1] + edges[1:])
    profile = np.zeros(bins, dtype=float)
    for index in range(bins):
        mask = (radius >= edges[index]) & (radius < edges[index + 1])
        profile[index] = float(np.mean(image[mask])) if np.any(mask) else 0.0
    peak = float(np.max(profile))
    if peak > 0:
        profile = profile / peak
    return centers, profile


def estimate_fwhm(radius: np.ndarray, profile: np.ndarray) -> float:
    """Estimate full width at half maximum for a radial profile."""

    if profile.size == 0 or not np.isfinite(profile).any() or np.max(profile) <= 0:
        return float("nan")
    above = np.where(profile >= 0.5 * np.max(profile))[0]
    if above.size < 2:
        return float("nan")
    return float(radius[above[-1]] - radius[above[0]])


def fit_ring_profile(matrix: np.ndarray) -> dict:
    """Extract a descriptive Gaussian-ring profile estimate in pixel units."""

    radius, profile = radial_profile(matrix)
    peak_index = int(np.argmax(profile))
    peak_radius = float(radius[peak_index])
    positive = np.clip(profile - float(np.min(profile)), 0.0, None)
    total = float(np.sum(positive))
    if total <= 0:
        sigma = float("nan")
    else:
        sigma = float(
            np.sqrt(np.sum(positive * (radius - peak_radius) ** 2) / total)
        )
    return {
        "radius_px": radius,
        "profile": profile,
        "peak_radius_px": peak_radius,
        "fwhm_px": estimate_fwhm(radius, profile),
        "gaussian_sigma_px": sigma,
    }


def estimate_eccentricity(matrix: np.ndarray) -> float:
    """Estimate intensity-weighted ellipse eccentricity after background subtraction."""

    weights = subtract_background(matrix)
    total = float(np.sum(weights))
    if total <= 0.0:
        return float("nan")
    center_x, center_y = estimate_center(weights)
    y, x = np.indices(weights.shape)
    dx = x - center_x
    dy = y - center_y
    covariance = np.array(
        [
            [np.sum(weights * dx * dx), np.sum(weights * dx * dy)],
            [np.sum(weights * dx * dy), np.sum(weights * dy * dy)],
        ]
    ) / total
    eigenvalues = np.sort(np.linalg.eigvalsh(covariance))
    if eigenvalues[1] <= 0.0:
        return float("nan")
    return float(np.sqrt(max(0.0, 1.0 - eigenvalues[0] / eigenvalues[1])))


def _select_representative_matrix(
    matrices: list[tuple[str, np.ndarray]],
) -> tuple[str, np.ndarray] | None:
    if not matrices:
        return None
    square_like = [
        item
        for item in matrices
        if abs(item[1].shape[0] - item[1].shape[1]) <= 0.1 * max(item[1].shape)
    ]
    candidates = square_like or matrices
    return max(candidates, key=lambda item: min(item[1].shape))


def write_spatial_eccentricity_summary(
    output_path: str | Path,
    literature_rows: list[dict],
    simulated_eccentricity: float,
) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "crystal",
        "experiment_eccentricity",
        "theory_eccentricity",
        "statistical_error",
        "systematic_error",
        "source",
        "notes",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in literature_rows:
            writer.writerow({**row, "notes": "Reported Table 1 value."})
        writer.writerow(
            {
                "crystal": "BBO_model_this_package",
                "experiment_eccentricity": "",
                "theory_eccentricity": simulated_eccentricity,
                "statistical_error": "",
                "systematic_error": "",
                "source": "bbo_spdc.ring simulation",
                "notes": "Intensity-moment estimate for the simulated ring.",
            }
        )
    return output_path


def plot_spatial_ring_validation(
    config: SPDCConfig,
    matrices: list[tuple[str, np.ndarray]],
    output_path: str | Path,
    eccentricity_path: str | Path,
    literature_eccentricity_rows: list[dict],
) -> dict:
    """Plot a deliberately qualitative comparison with public spatial data."""

    selected = _select_representative_matrix(matrices)
    simulation = simulate_spdc_ring_image(config, pixels=199, azimuthal_modulation=0.0)
    simulated_profile = fit_ring_profile(simulation.image)
    simulated_eccentricity = estimate_eccentricity(simulation.image)
    write_spatial_eccentricity_summary(
        eccentricity_path, literature_eccentricity_rows, simulated_eccentricity
    )

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.3))
    if selected is None:
        axes[0].axis("off")
        axes[0].text(
            0.5,
            0.5,
            "No readable Glasgow numeric matrix found.",
            ha="center",
            va="center",
        )
        experimental_report = {
            "experimental_matrix": "",
            "representative_profile_peak_px": None,
            "representative_profile_fwhm_px": None,
        }
        axes[2].text(
            0.5, 0.5, "Experimental radial profile unavailable.", ha="center", va="center"
        )
    else:
        name, matrix = selected
        processed = subtract_background(matrix)
        experimental_profile = fit_ring_profile(processed)
        image = axes[0].imshow(processed, origin="lower", cmap="magma", aspect="equal")
        fig.colorbar(image, ax=axes[0], fraction=0.046, pad=0.04)
        axes[0].set_title(f"Experimental spatial matrix\n{Path(name).stem}")
        axes[0].set_xlabel("pixel x")
        axes[0].set_ylabel("pixel y")

        experimental_radius = experimental_profile["radius_px"]
        experimental_radius = experimental_radius / max(float(np.max(experimental_radius)), 1.0)
        model_radius = simulated_profile["radius_px"]
        model_radius = model_radius / max(float(np.max(model_radius)), 1.0)
        axes[2].plot(
            experimental_radius,
            experimental_profile["profile"],
            color="#111827",
            linewidth=1.8,
            label="Glasgow representative matrix",
        )
        axes[2].plot(
            model_radius,
            simulated_profile["profile"],
            color="#b45309",
            linewidth=2.0,
            label="Type-I ring model",
        )
        axes[2].set_title("Normalized radial profiles")
        axes[2].set_xlabel("Normalized radial coordinate")
        axes[2].set_ylabel("Normalized intensity")
        axes[2].legend(fontsize=8)
        axes[2].text(
            0.04,
            0.05,
            "No shared optical radius calibration;\nno direct RMSE reported.",
            transform=axes[2].transAxes,
            fontsize=8.5,
        )
        experimental_report = {
            "experimental_matrix": name,
            "representative_profile_peak_px": experimental_profile["peak_radius_px"],
            "representative_profile_fwhm_px": experimental_profile["fwhm_px"],
        }

    model_image = axes[1].imshow(simulation.image, origin="lower", cmap="magma", aspect="equal")
    fig.colorbar(model_image, ax=axes[1], fraction=0.046, pad=0.04)
    axes[1].set_title("Simulated far-field ring")
    axes[1].set_xlabel("pixel x")
    axes[1].set_ylabel("pixel y")
    fig.suptitle("Qualitative spatial comparison: public Glasgow matrix and Type-I BBO ring model")
    fig.text(
        0.01,
        0.01,
        "Glasgow matrices are spatial-entanglement figure data, not a calibrated free-space ring scan.",
        fontsize=8.5,
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout(rect=[0.0, 0.045, 1.0, 0.94])
    fig.savefig(output_path, dpi=220)
    plt.close(fig)
    return {
        "metric_type": "qualitative_spatial_comparison",
        "source_url": GLASGOW_SOURCE_URL,
        "usable_matrix_count": len(matrices),
        **experimental_report,
        "model_peak_radius_px": simulated_profile["peak_radius_px"],
        "model_fwhm_px": simulated_profile["fwhm_px"],
        "model_eccentricity": simulated_eccentricity,
        "normalized_rmse": None,
        "radius_error_percent": None,
        "note": (
            "No direct radius/error metric is reported because the Glasgow matrices "
            "are not a calibrated far-field ring dataset."
        ),
    }
