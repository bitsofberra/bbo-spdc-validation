"""Type-I BBO SPDC phase-matching calculations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from math import asin, cos, degrees, isfinite, pi, radians, sin
from typing import Iterable

import numpy as np

from .constants import TWO_PI
from .sellmeier import (
    extraordinary_effective_index,
    extraordinary_index,
    ordinary_index,
    walkoff_angle_rad,
)


@dataclass(frozen=True)
class SPDCConfig:
    """Default configuration for degenerate Type-I SPDC in BBO."""

    pump_wavelength_m: float = 405e-9
    signal_wavelength_m: float = 810e-9
    idler_wavelength_m: float = 810e-9
    theta_deg: float = 28.95
    crystal_length_m: float = 2e-3
    pump_waist_m: float = 388e-6

    @property
    def theta_rad(self) -> float:
        return radians(self.theta_deg)

    def with_theta(self, theta_deg: float) -> "SPDCConfig":
        return replace(self, theta_deg=theta_deg)

    def with_signal_wavelength(self, signal_wavelength_m: float) -> "SPDCConfig":
        idler_wavelength_m = idler_wavelength_from_energy(
            self.pump_wavelength_m, signal_wavelength_m
        )
        return replace(
            self,
            signal_wavelength_m=signal_wavelength_m,
            idler_wavelength_m=idler_wavelength_m,
        )


def wavelength_m_to_nm(wavelength_m: float) -> float:
    return wavelength_m * 1e9


def nm_to_wavelength_m(wavelength_nm: float) -> float:
    return wavelength_nm * 1e-9


def idler_wavelength_from_energy(pump_wavelength_m: float, signal_wavelength_m: float):
    """Return idler wavelength from 1/lambda_p = 1/lambda_s + 1/lambda_i."""

    inverse_idler = 1.0 / pump_wavelength_m - 1.0 / signal_wavelength_m
    if np.any(inverse_idler <= 0):
        raise ValueError("Signal wavelength must be longer than the pump wavelength.")
    return 1.0 / inverse_idler


def ordinary_wave_number(wavelength_m):
    return TWO_PI * ordinary_index(wavelength_m) / wavelength_m


def pump_wave_number_extraordinary(wavelength_m, theta_rad):
    return TWO_PI * extraordinary_effective_index(wavelength_m, theta_rad) / wavelength_m


def delta_k_collinear_type1(
    theta_rad,
    pump_wavelength_m: float,
    signal_wavelength_m: float,
    idler_wavelength_m: float,
):
    """Longitudinal Delta k for e -> o + o Type-I SPDC."""

    return (
        ordinary_wave_number(signal_wavelength_m)
        + ordinary_wave_number(idler_wavelength_m)
        - pump_wave_number_extraordinary(pump_wavelength_m, theta_rad)
    )


def delta_k_noncollinear_type1(
    theta_rad,
    internal_emission_angle_rad,
    pump_wavelength_m: float,
    signal_wavelength_m: float,
    idler_wavelength_m: float,
):
    """Symmetric non-collinear Type-I Delta k along the pump direction."""

    phi = np.asarray(internal_emission_angle_rad, dtype=float)
    return (
        ordinary_wave_number(signal_wavelength_m) * np.cos(phi)
        + ordinary_wave_number(idler_wavelength_m) * np.cos(phi)
        - pump_wave_number_extraordinary(pump_wavelength_m, theta_rad)
    )


def phase_matching_sinc2(delta_k, crystal_length_m: float):
    """Return sinc^2(Delta k L / 2), using NumPy's normalized sinc."""

    argument = np.asarray(delta_k, dtype=float) * crystal_length_m / (2.0 * pi)
    return np.sinc(argument) ** 2


def coherence_length_m(delta_k: float) -> float:
    if abs(delta_k) < 1e-12:
        return float("inf")
    return pi / abs(delta_k)


def _bisect_root(function, low: float, high: float, tolerance: float, max_iter: int):
    f_low = float(function(low))
    f_high = float(function(high))
    if f_low == 0.0:
        return low
    if f_high == 0.0:
        return high
    if f_low * f_high > 0:
        raise ValueError("Root is not bracketed.")

    a, b = low, high
    for _ in range(max_iter):
        mid = 0.5 * (a + b)
        f_mid = float(function(mid))
        if abs(f_mid) < tolerance or abs(b - a) < tolerance:
            return mid
        if f_low * f_mid <= 0:
            b = mid
            f_high = f_mid
        else:
            a = mid
            f_low = f_mid
    return 0.5 * (a + b)


def find_type1_phase_matching_angle_deg(
    config: SPDCConfig,
    min_deg: float = 0.1,
    max_deg: float = 89.9,
    scan_points: int = 2000,
) -> float:
    """Find the collinear Type-I phase-matching theta angle in degrees."""

    def f(theta_rad):
        return delta_k_collinear_type1(
            theta_rad,
            config.pump_wavelength_m,
            config.signal_wavelength_m,
            config.idler_wavelength_m,
        )

    theta_grid = np.linspace(radians(min_deg), radians(max_deg), scan_points)
    values = f(theta_grid)
    for left, right, f_left, f_right in zip(
        theta_grid[:-1], theta_grid[1:], values[:-1], values[1:]
    ):
        if not (isfinite(float(f_left)) and isfinite(float(f_right))):
            continue
        if float(f_left) == 0.0:
            return degrees(float(left))
        if float(f_left) * float(f_right) < 0:
            root = _bisect_root(f, float(left), float(right), 1e-13, 100)
            return degrees(root)
    raise ValueError("No Type-I phase-matching angle found in the requested range.")


def find_internal_emission_angle_deg(
    config: SPDCConfig,
    theta_deg: float | None = None,
    max_internal_deg: float = 12.0,
) -> float:
    """Find symmetric internal emission angle for a theta value."""

    theta_rad = radians(config.theta_deg if theta_deg is None else theta_deg)

    def f(phi_rad):
        return delta_k_noncollinear_type1(
            theta_rad,
            phi_rad,
            config.pump_wavelength_m,
            config.signal_wavelength_m,
            config.idler_wavelength_m,
        )

    low = 0.0
    high = radians(max_internal_deg)
    f_low = float(f(low))
    f_high = float(f(high))
    if abs(f_low) < 1e-6:
        return 0.0
    if f_low * f_high > 0:
        return float("nan")
    return degrees(_bisect_root(f, low, high, 1e-13, 100))


def external_angle_deg(config: SPDCConfig, internal_angle_deg: float) -> float:
    """Convert internal BBO emission angle to external angle in air."""

    if not isfinite(internal_angle_deg):
        return float("nan")
    no_signal = float(ordinary_index(config.signal_wavelength_m))
    value = no_signal * sin(radians(internal_angle_deg))
    if abs(value) > 1.0:
        return float("nan")
    return degrees(asin(value))


def phase_matching_report(config: SPDCConfig) -> dict:
    """Return a JSON-serializable report for the current configuration."""

    theta_root_deg = find_type1_phase_matching_angle_deg(config)
    delta_k_current = float(
        delta_k_collinear_type1(
            config.theta_rad,
            config.pump_wavelength_m,
            config.signal_wavelength_m,
            config.idler_wavelength_m,
        )
    )
    delta_k_root = float(
        delta_k_collinear_type1(
            radians(theta_root_deg),
            config.pump_wavelength_m,
            config.signal_wavelength_m,
            config.idler_wavelength_m,
        )
    )
    internal_angle = find_internal_emission_angle_deg(config)
    rho = float(walkoff_angle_rad(config.pump_wavelength_m, config.theta_rad))
    walkoff_shift_m = config.crystal_length_m * np.tan(rho)

    return {
        "config": {
            "pump_wavelength_nm": wavelength_m_to_nm(config.pump_wavelength_m),
            "signal_wavelength_nm": wavelength_m_to_nm(config.signal_wavelength_m),
            "idler_wavelength_nm": wavelength_m_to_nm(config.idler_wavelength_m),
            "theta_deg": config.theta_deg,
            "crystal_length_mm": config.crystal_length_m * 1e3,
            "pump_waist_um": config.pump_waist_m * 1e6,
        },
        "indices": {
            "pump_n_o": float(ordinary_index(config.pump_wavelength_m)),
            "pump_n_e": float(extraordinary_index(config.pump_wavelength_m)),
            "pump_n_eff_at_theta": float(
                extraordinary_effective_index(config.pump_wavelength_m, config.theta_rad)
            ),
            "signal_n_o": float(ordinary_index(config.signal_wavelength_m)),
            "idler_n_o": float(ordinary_index(config.idler_wavelength_m)),
        },
        "phase_matching": {
            "theta_collinear_deg": theta_root_deg,
            "delta_k_current_rad_per_m": delta_k_current,
            "delta_k_at_root_rad_per_m": delta_k_root,
            "sinc2_current": float(
                phase_matching_sinc2(delta_k_current, config.crystal_length_m)
            ),
            "coherence_length_current_mm": coherence_length_m(delta_k_current) * 1e3,
            "internal_emission_angle_deg": internal_angle,
            "external_emission_angle_deg": external_angle_deg(config, internal_angle),
        },
        "walkoff": {
            "rho_mrad": rho * 1000.0,
            "lateral_shift_um": float(walkoff_shift_m * 1e6),
            "shift_over_pump_waist": float(walkoff_shift_m / config.pump_waist_m),
        },
    }


def sinc2_spectrum(
    config: SPDCConfig,
    signal_min_nm: float = 760.0,
    signal_max_nm: float = 860.0,
    points: int = 800,
):
    signal_nm = np.linspace(signal_min_nm, signal_max_nm, points)
    signal_m = signal_nm * 1e-9
    idler_m = idler_wavelength_from_energy(config.pump_wavelength_m, signal_m)
    delta_k = delta_k_collinear_type1(
        config.theta_rad, config.pump_wavelength_m, signal_m, idler_m
    )
    return signal_nm, idler_m * 1e9, phase_matching_sinc2(delta_k, config.crystal_length_m)


def theta_tuning_table(
    config: SPDCConfig,
    theta_values_deg: Iterable[float],
    signal_min_nm: float = 760.0,
    signal_max_nm: float = 880.0,
    spectrum_points: int = 600,
) -> list[dict]:
    rows: list[dict] = []
    signal_nm = np.linspace(signal_min_nm, signal_max_nm, spectrum_points)
    signal_m = signal_nm * 1e-9
    idler_m = idler_wavelength_from_energy(config.pump_wavelength_m, signal_m)

    for theta_deg in theta_values_deg:
        theta_rad = radians(theta_deg)
        delta_k = delta_k_collinear_type1(
            theta_rad, config.pump_wavelength_m, signal_m, idler_m
        )
        sinc2 = phase_matching_sinc2(delta_k, config.crystal_length_m)
        peak_index = int(np.argmax(sinc2))
        tuned_config = config.with_theta(float(theta_deg))
        internal_angle = find_internal_emission_angle_deg(tuned_config)
        rows.append(
            {
                "theta_deg": float(theta_deg),
                "peak_signal_nm": float(signal_nm[peak_index]),
                "peak_idler_nm": float(idler_m[peak_index] * 1e9),
                "peak_sinc2": float(sinc2[peak_index]),
                "internal_emission_angle_deg": float(internal_angle),
                "external_emission_angle_deg": float(
                    external_angle_deg(tuned_config, internal_angle)
                ),
            }
        )
    return rows


def config_to_dict(config: SPDCConfig) -> dict:
    data = asdict(config)
    return {
        "pump_wavelength_nm": data["pump_wavelength_m"] * 1e9,
        "signal_wavelength_nm": data["signal_wavelength_m"] * 1e9,
        "idler_wavelength_nm": data["idler_wavelength_m"] * 1e9,
        "theta_deg": data["theta_deg"],
        "crystal_length_mm": data["crystal_length_m"] * 1e3,
        "pump_waist_um": data["pump_waist_m"] * 1e6,
    }
