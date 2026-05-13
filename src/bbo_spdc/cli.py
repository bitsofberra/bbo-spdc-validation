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
    read_polarization_csv,
    read_power_scan_csv,
    read_experimental_csv,
    write_csv,
    write_json,
    write_phase_matching_summary,
)
from .phase_matching import SPDCConfig, nm_to_wavelength_m, phase_matching_report
from .polarization import compare_polarization_rows
from .ring import read_experimental_matrix, simulate_spdc_ring_image
from .spatial_data import (
    read_zip_text_matrices,
    summarize_matrices,
    write_spatial_summary_csv,
)


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
        plot_ring_simulation,
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
    plot_ring_simulation(simulate_spdc_ring_image(config), output / "spdc_ring_simulation.png")

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


def run_compare_polarization(args: argparse.Namespace) -> None:
    from .plots import plot_polarization_comparison

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)

    rows = read_polarization_csv(args.polarization_data)
    if not rows:
        print("Polarization CSV has no rows.")
        return

    predictions, report = compare_polarization_rows(rows)
    write_csv(output / "polarization_predictions.csv", predictions)
    write_json(output / "polarization_report.json", {"polarization_fit": report})
    plot_polarization_comparison(predictions, output / "polarization_comparison.png")
    print(f"Wrote polarization comparison outputs to {output}")
    print(f"Balanced Phi+ R^2: {report['ideal_phi_plus_r_squared']:.3f}")
    print(f"Unbalanced Bell-state R^2: {report['r_squared']:.3f}")


def run_summarize_spatial(args: argparse.Namespace) -> None:
    from .plots import plot_spatial_matrix_examples

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)

    matrices = read_zip_text_matrices(args.zip_data)
    if not matrices:
        print("No text matrices found in the spatial data archive.")
        return

    summaries = summarize_matrices(matrices)
    write_spatial_summary_csv(output / "spatial_matrix_summary.csv", summaries)
    plot_spatial_matrix_examples(
        matrices,
        output / "spatial_matrix_examples.png",
        max_items=args.max_plots,
    )
    print(f"Wrote spatial data summary outputs to {output}")
    print(f"Found {len(matrices)} experimental matrices")


def _ring_from_args(args: argparse.Namespace):
    config = _config_from_args(args)
    return simulate_spdc_ring_image(
        config,
        detector_distance_mm=args.detector_distance_mm,
        field_of_view_mm=args.field_of_view_mm,
        pixels=args.pixels,
        ring_width_mm=args.ring_width_mm,
        azimuthal_modulation=args.azimuthal_modulation,
    )


def run_simulate_ring(args: argparse.Namespace) -> None:
    from .plots import plot_ring_simulation

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    ring = _ring_from_args(args)
    plot_ring_simulation(ring, output / "spdc_ring_simulation.png")
    write_json(
        output / "spdc_ring_report.json",
        {
            "external_angle_deg": ring.external_angle_deg,
            "detector_distance_mm": ring.detector_distance_mm,
            "field_of_view_mm": ring.field_of_view_mm,
            "ring_radius_mm": ring.radius_mm,
            "ring_width_mm": ring.width_mm,
            "walkoff_shift_mm": ring.walkoff_shift_mm,
        },
    )
    print(f"Wrote simulated ring outputs to {output}")
    print(f"External angle: {ring.external_angle_deg:.3f} deg")
    print(f"Ring radius at detector: {ring.radius_mm:.3f} mm")


def run_compare_ring(args: argparse.Namespace) -> None:
    from .plots import plot_ring_comparison

    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    experiment = read_experimental_matrix(args.experimental_matrix)
    args.pixels = int(experiment.shape[0])
    ring = _ring_from_args(args)
    _, metrics = plot_ring_comparison(
        experiment,
        ring,
        output / "ring_experiment_vs_simulation.png",
    )
    write_json(
        output / "ring_comparison_report.json",
        {
            "comparison": metrics,
            "external_angle_deg": ring.external_angle_deg,
            "ring_radius_mm": ring.radius_mm,
            "ring_width_mm": ring.width_mm,
            "walkoff_shift_mm": ring.walkoff_shift_mm,
            "experimental_matrix_shape": list(experiment.shape),
        },
    )
    print(f"Wrote ring comparison outputs to {output}")
    print(f"Normalized RMSE: {metrics['rmse']:.3f}")


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

    polarization_parser = subparsers.add_parser(
        "compare-polarization",
        help="Compare polarizer-angle coincidences with a Phi+ Bell-state model.",
    )
    polarization_parser.add_argument(
        "--polarization-data",
        default="data/external/testing_reality_entanglement/data_allAngles.csv",
        help="CSV with polarizer angles, singles counts, and coincidence counts.",
    )
    polarization_parser.add_argument("--out", default="outputs/compare_polarization")
    polarization_parser.set_defaults(func=run_compare_polarization)

    spatial_parser = subparsers.add_parser(
        "summarize-spatial",
        help="Summarize public Type-I BBO spatial raw-data matrices from a zip archive.",
    )
    spatial_parser.add_argument(
        "--zip-data",
        default="data/external/glasgow_pixel_superresolution/Pixelsuperresolution.zip",
        help="Zip archive containing comma-separated text matrices.",
    )
    spatial_parser.add_argument("--out", default="outputs/summarize_spatial")
    spatial_parser.add_argument("--max-plots", type=int, default=6)
    spatial_parser.set_defaults(func=run_summarize_spatial)

    ring_parser = subparsers.add_parser(
        "simulate-ring",
        help="Generate a 2D far-field SPDC ring image from the phase-matching model.",
    )
    _add_config_args(ring_parser)
    ring_parser.add_argument("--out", default="outputs/ring")
    ring_parser.add_argument("--detector-distance-mm", type=float, default=100.0)
    ring_parser.add_argument("--field-of-view-mm", type=float, default=14.0)
    ring_parser.add_argument("--pixels", type=int, default=420)
    ring_parser.add_argument("--ring-width-mm", type=float, default=0.22)
    ring_parser.add_argument("--azimuthal-modulation", type=float, default=0.08)
    ring_parser.set_defaults(func=run_simulate_ring)

    ring_compare_parser = subparsers.add_parser(
        "compare-ring",
        help="Compare an experimental ring/image matrix with the simulated ring.",
    )
    _add_config_args(ring_compare_parser)
    ring_compare_parser.add_argument(
        "--experimental-matrix",
        required=True,
        help="2D CSV/TXT/NPY/image file containing an experimental ring or camera image.",
    )
    ring_compare_parser.add_argument("--out", default="outputs/compare_ring")
    ring_compare_parser.add_argument("--detector-distance-mm", type=float, default=100.0)
    ring_compare_parser.add_argument("--field-of-view-mm", type=float, default=14.0)
    ring_compare_parser.add_argument("--ring-width-mm", type=float, default=0.22)
    ring_compare_parser.add_argument("--azimuthal-modulation", type=float, default=0.08)
    ring_compare_parser.set_defaults(func=run_compare_ring)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
