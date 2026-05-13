"""Phenomenological entangled-photon counter model."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import radians
from statistics import median

import numpy as np

from .phase_matching import (
    SPDCConfig,
    delta_k_collinear_type1,
    phase_matching_sinc2,
)
from .sellmeier import walkoff_angle_rad


@dataclass(frozen=True)
class CounterSettings:
    """Adjustable detector and source parameters."""

    brightness_pairs_per_mw_s: float = 50_000.0
    signal_efficiency: float = 0.22
    idler_efficiency: float = 0.22
    signal_dark_rate_hz: float = 150.0
    idler_dark_rate_hz: float = 150.0
    coincidence_window_ns: float = 5.0

    def with_brightness(self, brightness_pairs_per_mw_s: float) -> "CounterSettings":
        return replace(self, brightness_pairs_per_mw_s=brightness_pairs_per_mw_s)


def walkoff_overlap(config: SPDCConfig) -> float:
    """Gaussian pump-overlap penalty caused by walk-off displacement."""

    rho = walkoff_angle_rad(config.pump_wavelength_m, config.theta_rad)
    shift = config.crystal_length_m * np.tan(rho)
    return float(np.exp(-((shift / config.pump_waist_m) ** 2)))


def relative_pair_factor(config: SPDCConfig) -> float:
    delta_k = delta_k_collinear_type1(
        config.theta_rad,
        config.pump_wavelength_m,
        config.signal_wavelength_m,
        config.idler_wavelength_m,
    )
    return float(phase_matching_sinc2(delta_k, config.crystal_length_m) * walkoff_overlap(config))


def expected_counts(
    config: SPDCConfig,
    pump_power_mw: float,
    integration_time_s: float,
    settings: CounterSettings | None = None,
) -> dict:
    """Predict singles and coincidence counts for one measurement point."""

    settings = settings or CounterSettings()
    pair_factor = relative_pair_factor(config)
    generated_pairs = (
        settings.brightness_pairs_per_mw_s
        * pump_power_mw
        * integration_time_s
        * pair_factor
    )
    true_coincidences = (
        generated_pairs * settings.signal_efficiency * settings.idler_efficiency
    )
    signal_counts = generated_pairs * settings.signal_efficiency
    idler_counts = generated_pairs * settings.idler_efficiency
    signal_counts += settings.signal_dark_rate_hz * integration_time_s
    idler_counts += settings.idler_dark_rate_hz * integration_time_s

    if integration_time_s > 0:
        signal_rate = signal_counts / integration_time_s
        idler_rate = idler_counts / integration_time_s
        accidentals = (
            signal_rate
            * idler_rate
            * settings.coincidence_window_ns
            * 1e-9
            * integration_time_s
        )
    else:
        accidentals = 0.0

    return {
        "theta_deg": config.theta_deg,
        "pair_factor": pair_factor,
        "generated_pairs": float(generated_pairs),
        "signal_counts": float(signal_counts),
        "idler_counts": float(idler_counts),
        "true_coincidence_counts": float(true_coincidences),
        "accidental_counts": float(accidentals),
        "coincidence_counts": float(true_coincidences + accidentals),
    }


def expected_counts_power_law(
    config: SPDCConfig,
    pump_power_mw: float,
    integration_time_s: float,
    brightness_pairs_per_mw_s: float,
    power_exponent: float,
    settings: CounterSettings | None = None,
) -> dict:
    """Predict counts with a calibrated power-law pump dependence."""

    settings = settings or CounterSettings()
    pair_factor = relative_pair_factor(config)
    generated_pairs = (
        brightness_pairs_per_mw_s
        * pump_power_mw**power_exponent
        * integration_time_s
        * pair_factor
    )
    true_coincidences = (
        generated_pairs * settings.signal_efficiency * settings.idler_efficiency
    )
    signal_counts = generated_pairs * settings.signal_efficiency
    idler_counts = generated_pairs * settings.idler_efficiency
    signal_counts += settings.signal_dark_rate_hz * integration_time_s
    idler_counts += settings.idler_dark_rate_hz * integration_time_s

    if integration_time_s > 0:
        signal_rate = signal_counts / integration_time_s
        idler_rate = idler_counts / integration_time_s
        accidentals = (
            signal_rate
            * idler_rate
            * settings.coincidence_window_ns
            * 1e-9
            * integration_time_s
        )
    else:
        accidentals = 0.0

    return {
        "theta_deg": config.theta_deg,
        "pump_power_mw": float(pump_power_mw),
        "power_exponent": float(power_exponent),
        "pair_factor": pair_factor,
        "generated_pairs": float(generated_pairs),
        "signal_counts": float(signal_counts),
        "idler_counts": float(idler_counts),
        "true_coincidence_counts": float(true_coincidences),
        "accidental_counts": float(accidentals),
        "coincidence_counts": float(true_coincidences + accidentals),
    }


def fit_brightness_from_experiment(
    rows: list[dict],
    base_config: SPDCConfig,
    settings: CounterSettings | None = None,
) -> float:
    """Estimate brightness from measured coincidence counts."""

    settings = settings or CounterSettings()
    estimates = []
    for row in rows:
        theta_deg = float(row["theta_deg"])
        pump_power_mw = float(row["pump_power_mw"])
        integration_time_s = float(row["integration_time_s"])
        measured = float(row["coincidence_counts"])
        config = base_config.with_theta(theta_deg)
        factor = relative_pair_factor(config)
        denominator = (
            pump_power_mw
            * integration_time_s
            * factor
            * settings.signal_efficiency
            * settings.idler_efficiency
        )
        if denominator > 0 and measured > 0:
            estimates.append(measured / denominator)

    if not estimates:
        return settings.brightness_pairs_per_mw_s
    return float(median(estimates))


def predictions_for_rows(
    rows: list[dict],
    base_config: SPDCConfig,
    settings: CounterSettings | None = None,
) -> list[dict]:
    """Return simulated counts matched to experimental rows."""

    settings = settings or CounterSettings()
    predictions = []
    for row in rows:
        theta_deg = float(row["theta_deg"])
        config = base_config.with_theta(theta_deg)
        prediction = expected_counts(
            config,
            pump_power_mw=float(row["pump_power_mw"]),
            integration_time_s=float(row["integration_time_s"]),
            settings=settings,
        )
        measured = float(row["coincidence_counts"])
        prediction["measured_coincidence_counts"] = measured
        prediction["residual_counts"] = measured - prediction["coincidence_counts"]
        if measured > 0:
            prediction["relative_error"] = prediction["residual_counts"] / measured
        else:
            prediction["relative_error"] = float("nan")
        predictions.append(prediction)
    return predictions


def fit_power_law_from_power_scan(
    rows: list[dict],
    base_config: SPDCConfig,
    settings: CounterSettings | None = None,
) -> tuple[float, float]:
    """Fit coincidence = brightness * power**exponent * detector terms."""

    settings = settings or CounterSettings()
    detector_factor = settings.signal_efficiency * settings.idler_efficiency
    pair_factor = relative_pair_factor(base_config)
    x_values = []
    y_values = []
    for row in rows:
        pump_power_mw = float(row["Pump_power_mW"])
        measured_hz = float(row["Coincidence_Hz"])
        denominator = pair_factor * detector_factor
        if pump_power_mw > 0 and measured_hz > 0 and denominator > 0:
            x_values.append(np.log(pump_power_mw))
            y_values.append(np.log(measured_hz / denominator))
    if len(x_values) < 2:
        return settings.brightness_pairs_per_mw_s, 1.0
    exponent, log_brightness = np.polyfit(x_values, y_values, deg=1)
    return float(np.exp(log_brightness)), float(exponent)


def predictions_for_power_scan(
    rows: list[dict],
    base_config: SPDCConfig,
    settings: CounterSettings | None = None,
) -> tuple[list[dict], dict]:
    """Return power-scan predictions and fitted calibration metadata."""

    settings = settings or CounterSettings()
    brightness, exponent = fit_power_law_from_power_scan(rows, base_config, settings)
    predictions = []
    for row in rows:
        prediction = expected_counts_power_law(
            base_config,
            pump_power_mw=float(row["Pump_power_mW"]),
            integration_time_s=1.0,
            brightness_pairs_per_mw_s=brightness,
            power_exponent=exponent,
            settings=settings,
        )
        measured = float(row["Coincidence_Hz"])
        prediction["measured_coincidence_hz"] = measured
        if row.get("Coincidence_error_Hz") not in (None, ""):
            prediction["measured_error_hz"] = float(row["Coincidence_error_Hz"])
        if row.get("Fit_Hz") not in (None, ""):
            prediction["source_fit_hz"] = float(row["Fit_Hz"])
        prediction["residual_hz"] = measured - prediction["coincidence_counts"]
        prediction["relative_error"] = (
            prediction["residual_hz"] / measured if measured > 0 else float("nan")
        )
        predictions.append(prediction)
    calibration = {
        "brightness_pairs_per_power_exponent_s": brightness,
        "power_exponent": exponent,
        "theta_deg": base_config.theta_deg,
    }
    return predictions, calibration
