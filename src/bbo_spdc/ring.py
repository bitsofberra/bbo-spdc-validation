"""Far-field SPDC ring image simulation and comparison helpers."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

import numpy as np

from .phase_matching import (
    SPDCConfig,
    external_angle_deg,
    find_internal_emission_angle_deg,
)
from .sellmeier import walkoff_angle_rad


@dataclass(frozen=True)
class RingSimulation:
    image: np.ndarray
    x_mm: np.ndarray
    y_mm: np.ndarray
    radius_mm: float
    width_mm: float
    external_angle_deg: float
    detector_distance_mm: float
    field_of_view_mm: float
    walkoff_shift_mm: float


def normalize_image(matrix: np.ndarray) -> np.ndarray:
    """Normalize a 2D image/matrix to the interval [0, 1]."""

    values = np.asarray(matrix, dtype=float)
    finite = np.isfinite(values)
    if not finite.any():
        return np.zeros_like(values, dtype=float)
    cleaned = np.where(finite, values, np.nan)
    minimum = float(np.nanmin(cleaned))
    maximum = float(np.nanmax(cleaned))
    if maximum <= minimum:
        return np.zeros_like(values, dtype=float)
    return np.nan_to_num((cleaned - minimum) / (maximum - minimum))


def simulate_spdc_ring_image(
    config: SPDCConfig,
    detector_distance_mm: float = 100.0,
    field_of_view_mm: float = 14.0,
    pixels: int = 420,
    ring_width_mm: float = 0.22,
    azimuthal_modulation: float = 0.08,
) -> RingSimulation:
    """Generate a simple far-field annular Type-I SPDC intensity image.

    The ring radius is set by the calculated external emission angle. The model
    is deliberately lightweight: it is meant for thesis-level visual comparison,
    not a full two-photon wavefunction propagation.
    """

    if pixels < 16:
        raise ValueError("pixels must be at least 16")
    if detector_distance_mm <= 0:
        raise ValueError("detector_distance_mm must be positive")
    if field_of_view_mm <= 0:
        raise ValueError("field_of_view_mm must be positive")
    if ring_width_mm <= 0:
        raise ValueError("ring_width_mm must be positive")

    internal_angle = find_internal_emission_angle_deg(config)
    angle_deg = external_angle_deg(config, internal_angle)
    if not isfinite(angle_deg):
        angle_deg = 0.0

    radius_mm = detector_distance_mm * np.tan(np.deg2rad(angle_deg))
    rho = float(walkoff_angle_rad(config.pump_wavelength_m, config.theta_rad))
    walkoff_shift_mm = config.crystal_length_m * np.tan(rho) * 1e3

    axis = np.linspace(-field_of_view_mm / 2.0, field_of_view_mm / 2.0, pixels)
    x_mm, y_mm = np.meshgrid(axis, axis)
    shifted_x = x_mm - walkoff_shift_mm
    r_mm = np.sqrt(shifted_x**2 + y_mm**2)
    phi = np.arctan2(y_mm, shifted_x)

    radial = np.exp(-0.5 * ((r_mm - radius_mm) / ring_width_mm) ** 2)
    angular = 1.0 + azimuthal_modulation * np.cos(2.0 * phi)
    aperture = np.exp(-0.5 * (r_mm / (0.48 * field_of_view_mm)) ** 6)
    image = normalize_image(radial * angular * aperture)

    return RingSimulation(
        image=image,
        x_mm=x_mm,
        y_mm=y_mm,
        radius_mm=float(radius_mm),
        width_mm=float(ring_width_mm),
        external_angle_deg=float(angle_deg),
        detector_distance_mm=float(detector_distance_mm),
        field_of_view_mm=float(field_of_view_mm),
        walkoff_shift_mm=float(walkoff_shift_mm),
    )


def read_experimental_matrix(path: str | Path) -> np.ndarray:
    """Read a text/CSV matrix or grayscale image for ring comparison."""

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix in {".txt", ".csv"}:
        matrix = np.loadtxt(path, delimiter=",")
    elif suffix == ".npy":
        matrix = np.load(path)
    elif suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        import matplotlib.image as mpimg

        matrix = mpimg.imread(path)
        if matrix.ndim == 3:
            matrix = matrix[..., :3].mean(axis=2)
    else:
        raise ValueError(f"Unsupported matrix/image format: {path.suffix}")

    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2:
        raise ValueError("Experimental ring input must be a 2D matrix or grayscale image.")
    return matrix


def ring_comparison_metrics(experiment: np.ndarray, simulation: np.ndarray) -> dict:
    """Return simple normalized residual metrics."""

    exp_norm = normalize_image(experiment)
    sim_norm = normalize_image(simulation)
    if exp_norm.shape != sim_norm.shape:
        raise ValueError("Experiment and simulation matrices must have the same shape.")
    residual = exp_norm - sim_norm
    rmse = float(np.sqrt(np.mean(residual**2)))
    if np.std(exp_norm) < 1e-12 or np.std(sim_norm) < 1e-12:
        correlation = float("nan")
    else:
        correlation = float(np.corrcoef(exp_norm.ravel(), sim_norm.ravel())[0, 1])
    return {
        "rmse": rmse,
        "correlation": correlation,
        "experiment_total_normalized": float(np.sum(exp_norm)),
        "simulation_total_normalized": float(np.sum(sim_norm)),
    }
