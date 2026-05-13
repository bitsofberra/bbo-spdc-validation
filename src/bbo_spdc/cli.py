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


def _fit_accuracy_percent(r_squared) -> float | str:
    try:
        value = float(r_squared)
    except (TypeError, ValueError):
        return ""
    if value != value:
        return ""
    return max(0.0, min(100.0, 100.0 * value))


def _format_accuracy_percent(r_squared) -> str:
    value = _fit_accuracy_percent(r_squared)
    if value == "":
        return ""
    return f"{value:.2f}"


def _prediction_fit_metrics(predictions: list[dict]) -> dict:
    measured = []
    simulated = []
    for row in predictions:
        measured.append(float(row["measured_coincidence_counts"]))
        simulated.append(float(row["coincidence_counts"]))
    if not measured:
        return {"r_squared": float("nan"), "rmse_counts": float("nan")}

    import numpy as np

    measured_values = np.asarray(measured, dtype=float)
    simulated_values = np.asarray(simulated, dtype=float)
    residual = measured_values - simulated_values
    ss_res = float(np.sum(residual**2))
    ss_tot = float(np.sum((measured_values - np.mean(measured_values)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {
        "r_squared": float(r_squared),
        "rmse_counts": float(np.sqrt(np.mean(residual**2))),
    }


def _write_accuracy_markdown(path: Path, rows: list[dict]) -> None:
    lines = [
        "# Thesis Run Accuracy Summary",
        "",
        "The percentage column is calculated from `R^2 * 100` where an `R^2` fit metric is available. "
        "Simulation-only figures do not have an experimental accuracy value.",
        "",
        "| Section | Dataset | Metric | Value | Fit accuracy (%) | Output |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {section} | {dataset} | {metric} | {value} | {accuracy_percent} | {output_dir} |".format(
                **row
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _run_public_polarization_dataset(
    dataset_name: str, data_path: str | Path, output: Path
) -> list[dict]:
    from .plots import plot_polarization_comparison

    rows = read_polarization_csv(data_path)
    predictions, report = compare_polarization_rows(rows)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "polarization_predictions.csv", predictions)
    write_json(output / "polarization_report.json", {"polarization_fit": report})
    plot_polarization_comparison(predictions, output / "polarization_comparison.png")
    return [
        {
            "section": "polarization",
            "dataset": dataset_name,
            "metric": "balanced_phi_plus_r_squared",
            "value": f"{report['ideal_phi_plus_r_squared']:.6f}",
            "accuracy_percent": _format_accuracy_percent(report["ideal_phi_plus_r_squared"]),
            "output_dir": str(output),
            "notes": "Balanced ideal Phi+ model fit.",
        },
        {
            "section": "polarization",
            "dataset": dataset_name,
            "metric": "unbalanced_bell_state_r_squared",
            "value": f"{report['r_squared']:.6f}",
            "accuracy_percent": _format_accuracy_percent(report["r_squared"]),
            "output_dir": str(output),
            "notes": "Best current accuracy value for this dataset.",
        },
        {
            "section": "polarization",
            "dataset": dataset_name,
            "metric": "rmse_counts",
            "value": f"{report['rmse_counts']:.6f}",
            "accuracy_percent": "",
            "output_dir": str(output),
            "notes": "Absolute residual scale in coincidence counts.",
        },
    ]


def run_thesis_run(args: argparse.Namespace) -> None:
    from .plots import (
        plot_counter_demo,
        plot_experiment_comparison,
        plot_power_scan_comparison,
        plot_ring_comparison,
        plot_ring_simulation,
        plot_sinc2_phase_matching,
        plot_spatial_matrix_examples,
        plot_theta_tuning_shift,
        plot_walkoff_effect,
    )

    config = _config_from_args(args)
    output = Path(args.out)
    output.mkdir(parents=True, exist_ok=True)
    summary_rows: list[dict] = []

    simulation_dir = output / "simulation"
    simulation_dir.mkdir(parents=True, exist_ok=True)
    report = phase_matching_report(config)
    write_json(simulation_dir / "phase_matching_report.json", report)
    write_phase_matching_summary(simulation_dir / "phase_matching_summary.txt", report)
    plot_sinc2_phase_matching(config, simulation_dir / "sinc2_phase_matching.png")
    plot_walkoff_effect(config, simulation_dir / "walkoff_effect.png")
    plot_theta_tuning_shift(config, simulation_dir / "theta_tuning_shift.png")
    plot_counter_demo(config, simulation_dir / "entangled_counter_demo.png")
    ring = _ring_from_args(args)
    plot_ring_simulation(ring, simulation_dir / "spdc_ring_simulation.png")
    write_json(
        simulation_dir / "spdc_ring_report.json",
        {
            "external_angle_deg": ring.external_angle_deg,
            "ring_radius_mm": ring.radius_mm,
            "ring_width_mm": ring.width_mm,
            "walkoff_shift_mm": ring.walkoff_shift_mm,
        },
    )
    summary_rows.extend(
        [
            {
                "section": "simulation",
                "dataset": "theory",
                "metric": "theta_collinear_deg",
                "value": f"{report['phase_matching']['theta_collinear_deg']:.6f}",
                "accuracy_percent": "",
                "output_dir": str(simulation_dir),
                "notes": "Theory-only output.",
            },
            {
                "section": "simulation",
                "dataset": "theory",
                "metric": "sinc2_current",
                "value": f"{report['phase_matching']['sinc2_current']:.6f}",
                "accuracy_percent": "",
                "output_dir": str(simulation_dir),
                "notes": "Phase-matching strength at configured theta; not an experimental accuracy.",
            },
            {
                "section": "simulation",
                "dataset": "theory",
                "metric": "ring_radius_mm",
                "value": f"{ring.radius_mm:.6f}",
                "accuracy_percent": "",
                "output_dir": str(simulation_dir),
                "notes": "Simulated ring radius at the configured detector distance.",
            },
        ]
    )

    public_sets = [
        ("Testing Reality", Path(args.testing_reality_data), output / "testing_reality_polarization"),
        ("EPJ Quantum Technology", Path(args.epj_data), output / "epj_polarization"),
    ]
    for dataset_name, data_path, dataset_output in public_sets:
        if data_path.exists():
            summary_rows.extend(
                _run_public_polarization_dataset(dataset_name, data_path, dataset_output)
            )

    glasgow_path = Path(args.glasgow_zip)
    if glasgow_path.exists():
        spatial_dir = output / "glasgow_spatial"
        matrices = read_zip_text_matrices(glasgow_path)
        summaries = summarize_matrices(matrices)
        write_spatial_summary_csv(spatial_dir / "spatial_matrix_summary.csv", summaries)
        plot_spatial_matrix_examples(
            matrices,
            spatial_dir / "spatial_matrix_examples.png",
            max_items=args.max_spatial_plots,
        )
        summary_rows.append(
            {
                "section": "spatial",
                "dataset": "University of Glasgow",
                "metric": "matrix_count",
                "value": str(len(matrices)),
                "accuracy_percent": "",
                "output_dir": str(spatial_dir),
                "notes": "Real Type-I BBO spatial raw-data archive; accuracy requires a matching image model.",
            }
        )

    experimental_path = Path(args.experimental)
    if experimental_path.exists():
        rows = read_experimental_csv(experimental_path)
        if rows:
            experimental_dir = output / "custom_experimental"
            initial_settings = CounterSettings()
            brightness = fit_brightness_from_experiment(rows, config, initial_settings)
            settings = initial_settings.with_brightness(brightness)
            predictions = predictions_for_rows(rows, config, settings)
            write_csv(experimental_dir / "comparison_predictions.csv", predictions)
            plot_experiment_comparison(
                predictions,
                experimental_dir / "experiment_vs_simulation.png",
            )
            metrics = _prediction_fit_metrics(predictions)
            summary_rows.append(
                {
                    "section": "custom_experimental",
                    "dataset": str(experimental_path),
                    "metric": "fitted_brightness_pairs_per_mw_s",
                    "value": f"{brightness:.6f}",
                    "accuracy_percent": "",
                    "output_dir": str(experimental_dir),
                    "notes": "Optional supervisor-provided angle/count table.",
                }
            )
            summary_rows.extend(
                [
                    {
                        "section": "custom_experimental",
                        "dataset": str(experimental_path),
                        "metric": "coincidence_r_squared",
                        "value": f"{metrics['r_squared']:.6f}",
                        "accuracy_percent": _format_accuracy_percent(metrics["r_squared"]),
                        "output_dir": str(experimental_dir),
                        "notes": "Agreement between measured and simulated coincidence counts.",
                    },
                    {
                        "section": "custom_experimental",
                        "dataset": str(experimental_path),
                        "metric": "rmse_counts",
                        "value": f"{metrics['rmse_counts']:.6f}",
                        "accuracy_percent": "",
                        "output_dir": str(experimental_dir),
                        "notes": "Absolute residual scale in coincidence counts.",
                    },
                ]
            )

    if args.ring_matrix:
        ring_dir = output / "ring_comparison"
        experiment = read_experimental_matrix(args.ring_matrix)
        args.pixels = int(experiment.shape[0])
        ring_for_shape = _ring_from_args(args)
        _, metrics = plot_ring_comparison(
            experiment,
            ring_for_shape,
            ring_dir / "ring_experiment_vs_simulation.png",
        )
        write_json(ring_dir / "ring_comparison_report.json", metrics)
        summary_rows.append(
            {
                "section": "ring",
                "dataset": str(args.ring_matrix),
                "metric": "normalized_rmse",
                "value": f"{metrics['rmse']:.6f}",
                "accuracy_percent": "",
                "output_dir": str(ring_dir),
                "notes": "Lower RMSE means closer normalized ring image match.",
            }
        )
        summary_rows.append(
            {
                "section": "ring",
                "dataset": str(args.ring_matrix),
                "metric": "image_correlation",
                "value": f"{metrics['correlation']:.6f}",
                "accuracy_percent": _format_accuracy_percent(metrics["correlation"]),
                "output_dir": str(ring_dir),
                "notes": "Correlation between normalized experimental and simulated images.",
            }
        )

    if args.include_proxy and Path(args.power_scan).exists():
        power_dir = output / "proxy_power_scan"
        rows = read_power_scan_csv(args.power_scan)
        predictions, calibration = predictions_for_power_scan(rows, config, CounterSettings())
        write_csv(power_dir / "power_scan_predictions.csv", predictions)
        plot_power_scan_comparison(predictions, power_dir / "power_scan_comparison.png")
        write_json(power_dir / "power_scan_report.json", {"power_scan_calibration": calibration})
        summary_rows.append(
            {
                "section": "proxy",
                "dataset": str(args.power_scan),
                "metric": "power_exponent",
                "value": f"{calibration['power_exponent']:.6f}",
                "accuracy_percent": "",
                "output_dir": str(power_dir),
                "notes": "Proxy/sample data only; do not use as final experimental evidence.",
            }
        )

    write_csv(output / "accuracy_summary.csv", summary_rows)
    write_json(output / "accuracy_summary.json", {"summary": summary_rows})
    _write_accuracy_markdown(output / "accuracy_summary.md", summary_rows)
    print(f"Wrote thesis run outputs to {output}")
    print(f"Accuracy summary: {output / 'accuracy_summary.md'}")


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

    thesis_parser = subparsers.add_parser(
        "thesis-run",
        help="Generate all thesis outputs and a single accuracy summary.",
    )
    _add_config_args(thesis_parser)
    thesis_parser.add_argument("--out", default="outputs/thesis_run")
    thesis_parser.add_argument(
        "--testing-reality-data",
        default="data/external/testing_reality_entanglement/data_allAngles.csv",
    )
    thesis_parser.add_argument(
        "--epj-data",
        default="data/external/epj_undergraduate_bell/phi_plus_table11.csv",
    )
    thesis_parser.add_argument(
        "--glasgow-zip",
        default="data/external/glasgow_pixel_superresolution/Pixelsuperresolution.zip",
    )
    thesis_parser.add_argument(
        "--experimental",
        default="data/experimental/experimental_counts.csv",
    )
    thesis_parser.add_argument("--ring-matrix", default="")
    thesis_parser.add_argument("--detector-distance-mm", type=float, default=100.0)
    thesis_parser.add_argument("--field-of-view-mm", type=float, default=14.0)
    thesis_parser.add_argument("--pixels", type=int, default=420)
    thesis_parser.add_argument("--ring-width-mm", type=float, default=0.22)
    thesis_parser.add_argument("--azimuthal-modulation", type=float, default=0.08)
    thesis_parser.add_argument("--max-spatial-plots", type=int, default=6)
    thesis_parser.add_argument("--include-proxy", action="store_true")
    thesis_parser.add_argument(
        "--power-scan",
        default="data/external/athleity_spdc_project/fit_data.csv",
    )
    thesis_parser.set_defaults(func=run_thesis_run)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
