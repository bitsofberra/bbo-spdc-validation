from bbo_spdc.polarization import (
    fit_phi_plus_counts,
    fit_unbalanced_correlated_counts,
    phi_plus_probability,
    unbalanced_correlated_probability,
)


def test_phi_plus_probability_is_maximum_for_parallel_polarizers():
    parallel = phi_plus_probability(0, 0)
    perpendicular = phi_plus_probability(0, 90)

    assert parallel == 0.5
    assert perpendicular < 1e-30


def test_phi_plus_fit_recovers_linear_scale_and_offset():
    alpha = [0, 0, 45, 45]
    beta = [0, 90, 45, -45]
    probabilities = phi_plus_probability(alpha, beta)
    counts = 1000 * probabilities + 12

    fit = fit_phi_plus_counts(alpha, beta, counts)

    assert abs(fit.scale - 1000) < 1e-9
    assert abs(fit.offset - 12) < 1e-9


def test_unbalanced_fit_recovers_biased_state_better_than_balanced_fit():
    alpha = [0, 0, 45, 45, 90, 90]
    beta = [0, 90, 45, -45, 90, 0]
    probability = unbalanced_correlated_probability(alpha, beta, 0.25, 0.0)
    counts = 1000 * probability + 10

    balanced = fit_phi_plus_counts(alpha, beta, counts)
    unbalanced = fit_unbalanced_correlated_counts(alpha, beta, counts)

    assert unbalanced.r_squared > balanced.r_squared
