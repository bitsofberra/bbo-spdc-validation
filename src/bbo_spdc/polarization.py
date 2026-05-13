"""Polarization-entanglement comparison models for BBO SPDC data."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PolarizationFit:
    scale: float
    offset: float
    r_squared: float
    rmse: float
    balance_hh: float | None = None
    phase_rad: float | None = None
    model: str = "balanced_phi_plus"


def phi_plus_probability(alpha_deg, beta_deg):
    """Ideal coincidence probability for |Phi+> after two linear polarizers."""

    alpha = np.deg2rad(np.asarray(alpha_deg, dtype=float))
    beta = np.deg2rad(np.asarray(beta_deg, dtype=float))
    return 0.5 * np.cos(alpha - beta) ** 2


def unbalanced_correlated_probability(alpha_deg, beta_deg, balance_hh: float, phase_rad: float):
    """Probability for sqrt(w)|HH> + exp(i phase)sqrt(1-w)|VV>."""

    alpha = np.deg2rad(np.asarray(alpha_deg, dtype=float))
    beta = np.deg2rad(np.asarray(beta_deg, dtype=float))
    horizontal = np.sqrt(balance_hh) * np.cos(alpha) * np.cos(beta)
    vertical = (
        np.sqrt(1.0 - balance_hh)
        * np.exp(1j * phase_rad)
        * np.sin(alpha)
        * np.sin(beta)
    )
    return np.abs(horizontal + vertical) ** 2


def _r_squared(measured, predicted) -> float:
    measured = np.asarray(measured, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    residual_sum = float(np.sum((measured - predicted) ** 2))
    total_sum = float(np.sum((measured - np.mean(measured)) ** 2))
    if total_sum <= 0:
        return float("nan")
    return 1.0 - residual_sum / total_sum


def fit_phi_plus_counts(alpha_deg, beta_deg, coincidence_counts) -> PolarizationFit:
    """Fit measured coincidences to offset + scale * P_PhiPlus(alpha, beta)."""

    p = phi_plus_probability(alpha_deg, beta_deg)
    y = np.asarray(coincidence_counts, dtype=float)
    design = np.column_stack([p, np.ones_like(p)])
    scale, offset = np.linalg.lstsq(design, y, rcond=None)[0]
    predicted = scale * p + offset
    rmse = float(np.sqrt(np.mean((y - predicted) ** 2)))
    return PolarizationFit(
        scale=float(scale),
        offset=float(offset),
        r_squared=_r_squared(y, predicted),
        rmse=rmse,
    )


def _fit_probability_model(probability, counts, model: str, balance_hh=None, phase_rad=None):
    y = np.asarray(counts, dtype=float)
    design = np.column_stack([probability, np.ones_like(probability)])
    scale, offset = np.linalg.lstsq(design, y, rcond=None)[0]
    predicted = scale * probability + offset
    rmse = float(np.sqrt(np.mean((y - predicted) ** 2)))
    return PolarizationFit(
        scale=float(scale),
        offset=float(offset),
        r_squared=_r_squared(y, predicted),
        rmse=rmse,
        balance_hh=None if balance_hh is None else float(balance_hh),
        phase_rad=None if phase_rad is None else float(phase_rad),
        model=model,
    )


def fit_unbalanced_correlated_counts(alpha_deg, beta_deg, coincidence_counts) -> PolarizationFit:
    """Grid-search a simple unbalanced correlated Bell-state model."""

    best: PolarizationFit | None = None
    for balance_hh in np.linspace(0.02, 0.98, 97):
        for phase_rad in np.linspace(-np.pi, np.pi, 73):
            probability = unbalanced_correlated_probability(
                alpha_deg, beta_deg, float(balance_hh), float(phase_rad)
            )
            fit = _fit_probability_model(
                probability,
                coincidence_counts,
                model="unbalanced_correlated",
                balance_hh=float(balance_hh),
                phase_rad=float(phase_rad),
            )
            if best is None or fit.r_squared > best.r_squared:
                best = fit
    if best is None:
        raise ValueError("Could not fit polarization model.")
    return best


def predict_phi_plus_counts(alpha_deg, beta_deg, fit: PolarizationFit):
    if fit.model == "unbalanced_correlated":
        if fit.balance_hh is None or fit.phase_rad is None:
            raise ValueError("Unbalanced fit requires balance_hh and phase_rad.")
        probability = unbalanced_correlated_probability(
            alpha_deg, beta_deg, fit.balance_hh, fit.phase_rad
        )
    else:
        probability = phi_plus_probability(alpha_deg, beta_deg)
    return fit.scale * probability + fit.offset


def compare_polarization_rows(rows: list[dict]) -> tuple[list[dict], dict]:
    alpha = np.array([row["alpha_deg"] for row in rows], dtype=float)
    beta = np.array([row["beta_deg"] for row in rows], dtype=float)
    measured = np.array([row["coincidence_counts"] for row in rows], dtype=float)
    ideal_fit = fit_phi_plus_counts(alpha, beta, measured)
    fit = fit_unbalanced_correlated_counts(alpha, beta, measured)
    predicted = predict_phi_plus_counts(alpha, beta, fit)
    ideal_probability = phi_plus_probability(alpha, beta)

    output_rows = []
    for source_row, probability, prediction in zip(rows, ideal_probability, predicted):
        measured_value = float(source_row["coincidence_counts"])
        row = dict(source_row)
        row["phi_plus_probability"] = float(probability)
        row["predicted_coincidence_counts"] = float(prediction)
        row["residual_counts"] = measured_value - float(prediction)
        row["relative_error"] = (
            row["residual_counts"] / measured_value if measured_value > 0 else float("nan")
        )
        output_rows.append(row)

    report = {
        "model": "offset + scale * |sqrt(w)cos(a)cos(b) + exp(i phase)sqrt(1-w)sin(a)sin(b)|^2",
        "ideal_phi_plus_model": "offset + scale * 0.5*cos(alpha-beta)^2",
        "ideal_phi_plus_r_squared": ideal_fit.r_squared,
        "ideal_phi_plus_rmse_counts": ideal_fit.rmse,
        "scale": fit.scale,
        "offset": fit.offset,
        "r_squared": fit.r_squared,
        "rmse_counts": fit.rmse,
        "balance_hh": fit.balance_hh,
        "balance_vv": None if fit.balance_hh is None else 1.0 - fit.balance_hh,
        "phase_rad": fit.phase_rad,
        "points": len(rows),
    }
    return output_rows, report
