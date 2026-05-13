"""BBO refractive-index utilities."""

from __future__ import annotations

import numpy as np


def _wavelength_um_squared(wavelength_m):
    wavelength_um = np.asarray(wavelength_m, dtype=float) * 1e6
    return wavelength_um**2


def ordinary_index(wavelength_m):
    """Ordinary refractive index of BBO from the Sellmeier equation."""

    lam2 = _wavelength_um_squared(wavelength_m)
    return np.sqrt(2.7405 + 0.0184 / (lam2 - 0.0179) - 0.0155 * lam2)


def extraordinary_index(wavelength_m):
    """Principal extraordinary refractive index of BBO."""

    lam2 = _wavelength_um_squared(wavelength_m)
    return np.sqrt(2.3730 + 0.0128 / (lam2 - 0.0156) - 0.0044 * lam2)


def extraordinary_effective_index(wavelength_m, theta_rad):
    """Effective extraordinary index for propagation angle theta."""

    no = ordinary_index(wavelength_m)
    ne = extraordinary_index(wavelength_m)
    theta = np.asarray(theta_rad, dtype=float)
    denominator = np.sqrt(no**2 * np.sin(theta) ** 2 + ne**2 * np.cos(theta) ** 2)
    return (no * ne) / denominator


def walkoff_alpha(wavelength_m, theta_rad):
    """Small-angle pump walk-off coefficient used in BBO SPDC models."""

    no = ordinary_index(wavelength_m)
    ne = extraordinary_index(wavelength_m)
    theta = np.asarray(theta_rad, dtype=float)
    numerator = (no**2 - ne**2) * np.sin(theta) * np.cos(theta)
    denominator = no**2 * np.sin(theta) ** 2 + ne**2 * np.cos(theta) ** 2
    return numerator / denominator


def walkoff_angle_rad(wavelength_m, theta_rad):
    """Pump Poynting-vector walk-off angle in radians."""

    return np.arctan(walkoff_alpha(wavelength_m, theta_rad))
