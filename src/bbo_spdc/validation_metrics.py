"""Validation metrics for model-to-experiment comparisons."""

from __future__ import annotations

import numpy as np


def r2_score(measured, predicted) -> float:
    """Return coefficient of determination for matched experimental values."""

    measured_values = np.asarray(measured, dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)
    residual_sum = float(np.sum((measured_values - predicted_values) ** 2))
    total_sum = float(np.sum((measured_values - np.mean(measured_values)) ** 2))
    if total_sum <= 0.0:
        return float("nan")
    return 1.0 - residual_sum / total_sum


def rmse(measured, predicted) -> float:
    """Return root-mean-square error."""

    residual = np.asarray(measured, dtype=float) - np.asarray(predicted, dtype=float)
    return float(np.sqrt(np.mean(residual**2)))


def mae(measured, predicted) -> float:
    """Return mean absolute error."""

    residual = np.asarray(measured, dtype=float) - np.asarray(predicted, dtype=float)
    return float(np.mean(np.abs(residual)))


def normalized_rmse(measured, predicted) -> float:
    """Return RMSE normalized to the measured data range."""

    measured_values = np.asarray(measured, dtype=float)
    value_range = float(np.nanmax(measured_values) - np.nanmin(measured_values))
    if value_range <= 0.0:
        return float("nan")
    return rmse(measured_values, predicted) / value_range


def poisson_sigma(counts):
    """Return Poisson counting uncertainty, sqrt(N), for nonnegative counts."""

    values = np.asarray(counts, dtype=float)
    return np.sqrt(np.clip(values, 0.0, None))


def weighted_rmse(measured, predicted, sigma) -> float:
    """Return root-mean-square residual in units of stated uncertainty."""

    measured_values = np.asarray(measured, dtype=float)
    predicted_values = np.asarray(predicted, dtype=float)
    sigma_values = np.asarray(sigma, dtype=float)
    valid = np.isfinite(sigma_values) & (sigma_values > 0.0)
    if not np.any(valid):
        return float("nan")
    normalized_residual = (
        measured_values[valid] - predicted_values[valid]
    ) / sigma_values[valid]
    return float(np.sqrt(np.mean(normalized_residual**2)))
