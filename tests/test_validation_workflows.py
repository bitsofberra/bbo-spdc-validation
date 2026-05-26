from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from bbo_spdc.data_loaders import load_epj_phi_plus_table11, load_karan_theta_digitized
from bbo_spdc.phase_matching import SPDCConfig
from bbo_spdc.polarization_validation import fit_polarization_model
from bbo_spdc.theta_validation import compare_theta_points, plot_theta_ring_validation
from bbo_spdc.thesis_outputs import run_clean_thesis_outputs


ROOT = Path(__file__).parents[1]


def test_polarization_fit_returns_finite_experimental_metrics():
    rows = load_epj_phi_plus_table11(
        ROOT / "data/external/epj_undergraduate_bell/phi_plus_table11.csv"
    )

    _, report = fit_polarization_model(rows, "EPJ")

    assert np.isfinite(report["r_squared_balanced"])
    assert np.isfinite(report["r_squared_unbalanced"])
    assert np.isfinite(report["rmse_unbalanced"])


def test_theta_validation_accepts_marker_rows_without_digitized_radii(tmp_path):
    rows = [
        {
            "theta_p_deg": 28.64,
            "experimental_ring_radius_mm_or_px": float("nan"),
            "model_ring_radius_mm_or_px": float("nan"),
        }
    ]
    report = compare_theta_points(rows)

    assert report["points"] == 0
    assert "not digitized" in report["warning"]

    plotted_report = plot_theta_ring_validation(
        SPDCConfig(), rows, tmp_path / "theta_ring_validation.png"
    )
    assert (tmp_path / "theta_ring_validation.png").exists()
    assert plotted_report["rmse"] is None


def test_theta_validation_reports_digitized_karan_annuli():
    rows = load_karan_theta_digitized(
        ROOT / "data/external/karan_bbo_phase_matching/type1_theta_emccd_digitized.csv"
    )
    report = compare_theta_points(rows)

    assert report["points"] == 2
    assert report["metric_type"] == "digitized_literature_data"
    assert report["unit"] == "figure_px"
    assert np.isclose(report["rmse"], 1.0)
    assert np.isclose(report["mae"], 1.0)
    assert report["direct_package_model_fit"] is False


def test_clean_thesis_run_generates_only_expected_main_figures(tmp_path):
    output = tmp_path / "thesis_run"
    run_clean_thesis_outputs(
        SPDCConfig(),
        output,
        ROOT / "data/external/epj_undergraduate_bell/phi_plus_table11.csv",
        ROOT / "data/external/testing_reality_entanglement/data_allAngles.csv",
        ROOT / "data/external/karan_bbo_phase_matching/type1_theta_emccd_digitized.csv",
        ROOT / "data/external/byu_noncollinear_spdc/byu_fig3_3_digitized.csv",
        ROOT / "data/external/glasgow_pixel_superresolution/Pixelsuperresolution.zip",
        ROOT / "data/external/josa_b_elliptical_rings/bbo_eccentricity_table1.csv",
    )

    main_png_files = {path.name for path in output.glob("*.png")}
    assert main_png_files == {
        "model_sinc2_phase_matching.png",
        "theta_ring_validation.png",
        "polarization_validation_epj_phi_plus.png",
        "polarization_validation_testing_reality.png",
        "spatial_ring_validation.png",
    }
    assert not (output / "entangled_counter_demo.png").exists()
    assert not (output / "spdc_ring_simulation.png").exists()

    summary = json.loads((output / "validation_summary.json").read_text(encoding="utf-8"))
    model_row = next(
        row for row in summary["figures"] if row["figure"] == "model_sinc2_phase_matching.png"
    )
    assert model_row["metric_type"] == "theory_only"
    assert model_row["r_squared_agreement_percent"] == ""
    theta_row = next(
        row for row in summary["figures"] if row["figure"] == "theta_ring_validation.png"
    )
    assert theta_row["metric_type"] == "digitized_literature_data"
    assert theta_row["r_squared_agreement_percent"] == ""
