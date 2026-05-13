"""Command-line interface for the BBO SPDC package."""

from __future__ import annotations

import argparse
from pathlib import Path

from .counter import (
    CounterSettings,
    fit_brightness_from_experiment,
    predictions_for_power_scan,
    predictions_for_rows,
)
from .data_io import (
    read_power_scan_csv,
    read_experimental_csv,
    write_csv,
    write_json,
    write_phase_matching_summary,
)
from .phase_matching import SPDCConfig, nm_to_wavelength_m, phase_matching_report


def _add_config_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pump-wavelength-nm", type=float, default=405.0)
    parser.add_argument("--signal-wavelength-nm", type=float, default=810.0)
    parser.add_argument("--idler-wavelength-nm", type=float, default=810.0)
    parser.add_argument("--theta-deg", type=float, default=28.95)
    parser.add_argument("--crystal-length-mm", type=float, default=2.0)
    parser.add_argument("--pump-waist-um", type=float, default=388.0)


def _config_from_args(args: argparse.Namespace) -> SPDCConfig:
    return SPDCConfig(
        pump_wavelength_m=nm_to_wavelength_m(args.pump_wavelength_nm),
        signal_wavelength_m=nm_to_wavelength_m(args.signal_wavelength_nm),
        idler_wavelength_m=nm_to_wavelength_m(args.idler_wavelength_nm),
        theta_deg=args.theta_deg,
        crystal_length_m=args.crystal_length_mm * 1e-3,
        pump_waist_m=args.pump_waist_um * 1e-6,
    )


def run_report(args: argparse.Namespace) -> None:
    config = _config_from_args(args)
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    report = phase_matching_report(config)
    write_json(output / "phase_matching_report.json", report)
    write_phase_matching_summary(output / "phase_matching_summary.txt", report)
    print(f"Wrote report to {output}")


def run_demo(args: argparse.Namespace) -> None:
    from .plots import (
        plot_counter_demo,
        plot_sinc2_phase_matching,
        plot_theta_tuning_shift,
        plot_walkoff_effect,
    )

    config = _config_from_args(args)
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)

    report = phase_matching_report(config)
    write_json(output / "phase_matching_report.json", report)
    write_phase_matching_summary(output / "phase_matching_summary.txt", report)
    plot_sinc2_phase_matching(config, output / "sinc2_phase_matching.png")
    plot_walkoff_effect(config, output / "walkoff_effect.png")
    plot_theta_tuning_shift(config, output / "theta_tuning_shift.png")
    plot_counter_demo(config, output / "entangled_counter_demo.png")

    print(f"Wrote demo outputs to {output}")
    print(
        "Collinear theta: "
        f"{report['phase_matching']['theta_collinear_deg']:.4f} deg"
    )
    print(f"Current sinc^2: {report['phase_matching']['sinc2_current']:.4f}")


def run_compare(args: argparse.Namespace) -> None:
    from .plots import plot_experiment_comparison

    config = _config_from_args(args)
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)

    rows = read_experimental_csv(args.experimental)
    if not rows:
        print(
            "Experimental CSV has no rows yet. "
            "Add measurements to data/experimental/experimental_counts.csv first."
        )
        return

    initial_settings = CounterSettings()
    brightness = fit_brightness_from_experiment(rows, config, initial_settings)
    settings = initial_settings.with_brightness(brightness)
    predictions = predictions_for_rows(rows, config, settings)
    write_csv(output / "comparison_predictions.csv", predictions)
    plot_experiment_comparison(predictions, output / "experiment_vs_simulation.png")

    report = phase_matching_report(config)
    report["counter_calibration"] = {
        "brightness_pairs_per_mw_s": brightness,
        "signal_efficiency": settings.signal_efficiency,
        "idler_efficiency": settings.idler_efficiency,
        "coincidence_window_ns": settings.coincidence_window_ns,
    }
    write_json(output / "comparison_report.json", report)
    print(f"Wrote comparison outputs to {output}")
    print(f"Fitted brightness: {brightness:.3f} pairs/(mW s)")


def run_compare_power(args: argparse.Namespace) -> None:
    from .plots import plot_power_scan_comparison

    config = _config_from_args(args)
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)

    rows = read_power_scan_csv(args.power_scan)
    if not rows:
        print("Power-scan CSV has no rows.")
        return

    predictions, calibration = predictions_for_power_scan(rows, config, CounterSettings())
    write_csv(output / "power_scan_predictions.csv", predictions)
    plot_power_scan_comparison(predictions, output / "power_scan_comparison.png")
    write_json(output / "power_scan_report.json", {"power_scan_calibration": calibration})
    print(f"Wrote power-scan comparison outputs to {output}")
    print(
        "Fitted power law: "
        f"coincidence ~ power^{calibration['power_exponent']:.3f}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bbo-spdc",
        description="Type-I BBO SPDC simulations and experimental comparison.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser("report", help="Calculate phase matching.")
    _add_config_args(report_parser)
    report_parser.add_argument("--out", default="outputs/report")
    report_parser.set_defaults(func=run_report)

    demo_parser = subparsers.add_parser("run-demo", help="Generate all baseline plots.")
    _add_config_args(demo_parser)
    demo_parser.add_argument("--out", default="outputs/demo")
    demo_parser.set_defaults(func=run_demo)

    compare_parser = subparsers.add_parser(
        "compare", help="Compare simulation with experimental CSV data."
    )
    _add_config_args(compare_parser)
    compare_parser.add_argument(
        "--experimental",
        default="data/experimental/experimental_counts.csv",
        help="CSV file with experimental count data.",
    )
    compare_parser.add_argument("--out", default="outputs/compare")
    compare_parser.set_defaults(func=run_compare)

    power_parser = subparsers.add_parser(
        "compare-power", help="Compare with pump-power vs coincidence data."
    )
    _add_config_args(power_parser)
    power_parser.add_argument(
        "--power-scan",
        default="data/external/athleity_spdc_project/fit_data.csv",
        help="CSV with Pump_power_mW and Coincidence_Hz columns.",
    )
    power_parser.add_argument("--out", default="outputs/compare_power")
    power_parser.set_defaults(func=run_compare_power)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
