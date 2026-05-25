from __future__ import annotations

import numpy as np

from bbo_spdc.validation_metrics import poisson_sigma, r2_score, rmse


def test_poisson_sigma_returns_square_root_counts():
    np.testing.assert_allclose(poisson_sigma([0.0, 4.0, 9.0]), [0.0, 2.0, 3.0])


def test_validation_metrics_are_finite_for_matching_series():
    measured = [1.0, 2.0, 3.0]
    predicted = [1.1, 1.9, 3.0]

    assert np.isfinite(r2_score(measured, predicted))
    assert np.isfinite(rmse(measured, predicted))
