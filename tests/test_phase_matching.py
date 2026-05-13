from math import isfinite

from bbo_spdc.phase_matching import (
    SPDCConfig,
    find_type1_phase_matching_angle_deg,
    phase_matching_report,
    phase_matching_sinc2,
)


def test_default_phase_matching_angle_is_in_expected_bbo_range():
    theta = find_type1_phase_matching_angle_deg(SPDCConfig())
    assert 28.0 < theta < 30.0


def test_sinc2_is_one_at_zero_mismatch():
    assert phase_matching_sinc2(0.0, 2e-3) == 1.0


def test_report_has_finite_current_values():
    report = phase_matching_report(SPDCConfig())
    assert isfinite(report["phase_matching"]["delta_k_current_rad_per_m"])
    assert report["phase_matching"]["sinc2_current"] >= 0.0
    assert 0.0 < report["walkoff"]["rho_mrad"] < 100.0
