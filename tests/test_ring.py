from __future__ import annotations

import numpy as np

from bbo_spdc.phase_matching import SPDCConfig
from bbo_spdc.ring import normalize_image, ring_comparison_metrics, simulate_spdc_ring_image


def test_ring_simulation_returns_normalized_square_image():
    ring = simulate_spdc_ring_image(SPDCConfig(), pixels=64)

    assert ring.image.shape == (64, 64)
    assert 0.0 <= ring.image.min() <= ring.image.max() <= 1.0
    assert ring.radius_mm >= 0.0


def test_normalize_image_handles_constant_matrix():
    normalized = normalize_image(np.ones((4, 4)))

    assert np.all(normalized == 0.0)


def test_ring_comparison_metrics_identical_images_have_zero_rmse():
    image = np.array([[0.0, 1.0], [1.0, 0.0]])
    metrics = ring_comparison_metrics(image, image)

    assert metrics["rmse"] == 0.0
    assert metrics["correlation"] > 0.99
