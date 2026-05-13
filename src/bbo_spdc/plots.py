"""Plot generation for BBO Type-I SPDC validation."""

from __future__ import annotations

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

from .counter import CounterSettings, expected_counts, relative_pair_factor, walkoff_overlap
from .phase_matching import (
    SPDCConfig,
    delta_k_collinear_type1,
    external_angle_deg,
    find_internal_emission_angle_deg,
    find_type1_phase_matching_angle_deg,
    phase_matching_sinc2,
    sinc2_spectrum,
)
from .sellmeier import walkoff_angle_rad


def _prepare_output(path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _set_style():
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 220,
            "font.size": 10,
            "axes.grid": True,
            "grid.alpha": 0.22,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def plot_sinc2_phase_matching(config: SPDCConfig, output_path: str | Path) -> Path:
    _set_style()
    signal_nm, idler_nm, sinc2 = sinc2_spectrum(config)
    peak_index = int(np.argmax(sinc2))

    mismatch = np.linspace(-4.0 * np.pi, 4.0 * np.pi, 900)
    universal = np.sinc(mismatch / np.pi) ** 2

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(10.8, 4.4))
    ax0.plot(mismatch, universal, color="#2563eb", linewidth=2.2)
    ax0.axvline(0.0, color="#111827", linestyle="--", linewidth=1.1)
    ax0.set_xlabel("Delta k L / 2")
    ax0.set_ylabel("sinc^2(Delta k L / 2)")
    ax0.set_title("Phase-matching envelope")
    ax0.text(
        0.04,
        0.92,
        "Maximum at Delta k = 0",
        transform=ax0.transAxes,
        va="top",
        color="#111827",
    )

    ax1.plot(signal_nm, sinc2, color="#0f766e", linewidth=2.2)
    ax1.axvline(signal_nm[peak_index], color="#b45309", linestyle="--", linewidth=1.3)
    ax1.set_xlabel("Signal wavelength (nm)")
    ax1.set_ylabel("sinc^2")
    ax1.set_title(f"Collinear spectrum at theta = {config.theta_deg:.2f} deg")
    ax1.text(
        0.04,
        0.92,
        (
            f"peak signal: {signal_nm[peak_index]:.2f} nm\n"
            f"idler: {idler_nm[peak_index]:.2f} nm\n"
            f"peak sinc^2: {sinc2[peak_index]:.4f}"
        ),
        transform=ax1.transAxes,
        va="top",
        color="#7c2d12",
        bbox={"facecolor": "white", "edgecolor": "#f3f4f6", "alpha": 0.85},
    )

    output_path = _prepare_output(output_path)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_walkoff_effect(config: SPDCConfig, output_path: str | Path) -> Path:
    _set_style()
    theta_deg = np.linspace(0.1, 60.0, 500)
    theta_rad = np.deg2rad(theta_deg)
    rho_rad = walkoff_angle_rad(config.pump_wavelength_m, theta_rad)
    shift_um = config.crystal_length_m * np.tan(rho_rad) * 1e6
    overlap = np.exp(-((shift_um * 1e-6 / config.pump_waist_m) ** 2))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.2))
    ax1.plot(theta_deg, rho_rad * 1000.0, color="#2563eb", linewidth=2.0)
    ax1.axvline(config.theta_deg, color="#6d28d9", linestyle="--", linewidth=1.2)
    ax1.set_xlabel("Theta (deg)")
    ax1.set_ylabel("Walk-off angle rho (mrad)")
    ax1.set_title("Pump walk-off")

    ax2.plot(theta_deg, shift_um, color="#b45309", linewidth=2.0, label="lateral shift")
    ax2.set_xlabel("Theta (deg)")
    ax2.set_ylabel("Lateral shift after crystal (um)")
    ax2b = ax2.twinx()
    ax2b.plot(theta_deg, overlap, color="#0f766e", linewidth=2.0, label="Gaussian overlap")
    ax2b.set_ylabel("Relative overlap")
    ax2.axvline(config.theta_deg, color="#6d28d9", linestyle="--", linewidth=1.2)
    ax2.set_title("Walk-off reduces collection overlap")

    lines = ax2.get_lines() + ax2b.get_lines()
    ax2.legend(lines, [line.get_label() for line in lines], loc="best")

    output_path = _prepare_output(output_path)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_theta_tuning_shift(config: SPDCConfig, output_path: str | Path) -> Path:
    _set_style()
    root = find_type1_phase_matching_angle_deg(config)
    theta_values = np.linspace(root - 0.45, root + 0.65, 80)
    theta_rad = np.deg2rad(theta_values)
    delta_k = delta_k_collinear_type1(
        theta_rad,
        config.pump_wavelength_m,
        config.signal_wavelength_m,
        config.idler_wavelength_m,
    )
    degenerate_strength = phase_matching_sinc2(delta_k, config.crystal_length_m)
    external_angle = np.array(
        [
            external_angle_deg(
                config.with_theta(float(theta)),
                find_internal_emission_angle_deg(config.with_theta(float(theta))),
            )
            for theta in theta_values
        ]
    )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.2))
    ax1.plot(theta_values, degenerate_strength, color="#0f766e", linewidth=2.0)
    ax1.axvline(config.theta_deg, color="#b45309", linestyle="--", linewidth=1.2)
    ax1.axvline(root, color="#111827", linestyle=":", linewidth=1.2)
    ax1.set_xlabel("Theta (deg)")
    ax1.set_ylabel("sinc^2 at 810 nm")
    ax1.set_title("Angular acceptance")
    ax1.text(
        0.04,
        0.92,
        f"collinear root: {root:.4f} deg",
        transform=ax1.transAxes,
        va="top",
        color="#111827",
    )

    ax2.plot(theta_values, external_angle, color="#7c3aed", linewidth=2.0)
    ax2.axvline(config.theta_deg, color="#b45309", linestyle="--", linewidth=1.2)
    ax2.set_xlabel("Theta (deg)")
    ax2.set_ylabel("External emission angle (deg)")
    ax2.set_title("Ring angle shift")

    output_path = _prepare_output(output_path)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_counter_demo(config: SPDCConfig, output_path: str | Path) -> Path:
    _set_style()
    root = find_type1_phase_matching_angle_deg(config)
    theta_values = np.linspace(root - 0.35, root + 0.35, 61)
    settings = CounterSettings()
    rows = [
        expected_counts(config.with_theta(float(theta)), 10.0, 1.0, settings)
        for theta in theta_values
    ]

    coincidence = np.array([row["coincidence_counts"] for row in rows])
    signal = np.array([row["signal_counts"] for row in rows])
    idler = np.array([row["idler_counts"] for row in rows])
    pair_factor = np.array([relative_pair_factor(config.with_theta(float(t))) for t in theta_values])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.2))
    ax1.plot(theta_values, signal, label="signal", color="#2563eb", linewidth=2.0)
    ax1.plot(theta_values, idler, label="idler", color="#0f766e", linewidth=2.0)
    ax1.plot(theta_values, coincidence, label="coincidence", color="#b45309", linewidth=2.0)
    ax1.set_yscale("log")
    ax1.set_xlabel("Theta (deg)")
    ax1.set_ylabel("Counts in 1 s at 10 mW")
    ax1.set_title("Entangled photon counter demo")
    ax1.legend()

    ax2.plot(theta_values, pair_factor, marker="o", color="#7c3aed", linewidth=2.0)
    ax2.set_xlabel("Theta (deg)")
    ax2.set_ylabel("Relative pair factor")
    ax2.set_title(f"Walk-off overlap at default theta: {walkoff_overlap(config):.3f}")

    output_path = _prepare_output(output_path)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_experiment_comparison(predictions: list[dict], output_path: str | Path) -> Path:
    _set_style()
    theta = np.array([row["theta_deg"] for row in predictions], dtype=float)
    measured = np.array([row["measured_coincidence_counts"] for row in predictions], dtype=float)
    simulated = np.array([row["coincidence_counts"] for row in predictions], dtype=float)
    residual = measured - simulated

    order = np.argsort(theta)
    theta = theta[order]
    measured = measured[order]
    simulated = simulated[order]
    residual = residual[order]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.4, 6.2), sharex=True)
    ax1.plot(theta, measured, marker="o", color="#111827", linewidth=1.8, label="experiment")
    ax1.plot(theta, simulated, marker="s", color="#0f766e", linewidth=1.8, label="simulation")
    ax1.set_ylabel("Coincidence counts")
    ax1.set_title("Experiment vs simulation")
    ax1.legend()

    ax2.axhline(0.0, color="#6b7280", linewidth=1.0)
    ax2.bar(theta, residual, width=0.03, color="#b45309")
    ax2.set_xlabel("Theta (deg)")
    ax2.set_ylabel("Experiment - simulation")

    output_path = _prepare_output(output_path)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_power_scan_comparison(predictions: list[dict], output_path: str | Path) -> Path:
    _set_style()
    power = np.array([row["pump_power_mw"] for row in predictions], dtype=float)
    measured = np.array([row["measured_coincidence_hz"] for row in predictions], dtype=float)
    simulated = np.array([row["coincidence_counts"] for row in predictions], dtype=float)
    source_fit = np.array(
        [row.get("source_fit_hz", np.nan) for row in predictions], dtype=float
    )
    residual = measured - simulated
    order = np.argsort(power)
    power = power[order]
    measured = measured[order]
    simulated = simulated[order]
    source_fit = source_fit[order]
    residual = residual[order]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.4, 6.2), sharex=True)
    ax1.plot(power, measured, marker="o", color="#111827", linewidth=1.8, label="sample/proxy data")
    ax1.plot(power, simulated, marker="s", color="#0f766e", linewidth=1.8, label="calibrated model")
    if np.isfinite(source_fit).any():
        ax1.plot(power, source_fit, color="#b45309", linestyle="--", linewidth=1.6, label="source fit")
    ax1.set_ylabel("Coincidence rate (Hz)")
    ax1.set_title("Pump power scan comparison")
    ax1.legend()

    ax2.axhline(0.0, color="#6b7280", linewidth=1.0)
    ax2.bar(power, residual, width=max(1.0, np.ptp(power) / 70.0), color="#7c3aed")
    ax2.set_xlabel("Pump power (mW)")
    ax2.set_ylabel("Data - model (Hz)")

    output_path = _prepare_output(output_path)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_polarization_comparison(predictions: list[dict], output_path: str | Path) -> Path:
    _set_style()
    alpha = np.array([row["alpha_deg"] for row in predictions], dtype=float)
    beta = np.array([row["beta_deg"] for row in predictions], dtype=float)
    measured = np.array([row["coincidence_counts"] for row in predictions], dtype=float)
    predicted = np.array([row["predicted_coincidence_counts"] for row in predictions], dtype=float)
    residual = measured - predicted

    unique_alpha = np.array(sorted(set(alpha)))
    unique_beta = np.array(sorted(set(beta)))

    def grid(values):
        matrix = np.full((len(unique_alpha), len(unique_beta)), np.nan)
        for a, b, value in zip(alpha, beta, values):
            i = int(np.where(unique_alpha == a)[0][0])
            j = int(np.where(unique_beta == b)[0][0])
            matrix[i, j] = value
        return matrix

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.2))
    panels = [
        (grid(measured), "Measured coincidences", "viridis"),
        (grid(predicted), "Fitted Bell-state model", "viridis"),
        (grid(residual), "Residuals", "coolwarm"),
    ]
    extent = [unique_beta.min(), unique_beta.max(), unique_alpha.min(), unique_alpha.max()]
    for ax, (matrix, title, cmap) in zip(axes, panels):
        image = ax.imshow(matrix, origin="lower", aspect="auto", extent=extent, cmap=cmap)
        ax.set_xlabel("Beta / PolB (deg)")
        ax.set_ylabel("Alpha / PolA (deg)")
        ax.set_title(title)
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

    output_path = _prepare_output(output_path)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_spatial_matrix_examples(
    matrices: list[tuple[str, np.ndarray]], output_path: str | Path, max_items: int = 6
) -> Path:
    """Plot example real experimental SPDC image matrices."""

    _set_style()
    selected = matrices[:max(1, max_items)]
    columns = min(3, len(selected))
    rows = int(np.ceil(len(selected) / columns))

    fig, axes = plt.subplots(rows, columns, figsize=(4.1 * columns, 3.6 * rows))
    axes_array = np.atleast_1d(axes).ravel()
    for ax, (name, matrix) in zip(axes_array, selected):
        image = ax.imshow(matrix, cmap="magma", origin="lower", aspect="auto")
        ax.set_title(Path(name).stem)
        ax.set_xlabel("pixel x")
        ax.set_ylabel("pixel y")
        fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)

    for ax in axes_array[len(selected) :]:
        ax.axis("off")

    output_path = _prepare_output(output_path)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path
