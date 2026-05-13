# Remaining Work

## Highest-Priority Scientific Gaps

1. Decide which public dataset becomes the main experimental comparison.

There is no in-house experimental setup, so the thesis should state that the
experimental comparison uses public BBO SPDC datasets. The strongest current
choices are:

- EPJ Quantum Technology Table 11 for Bell-state coincidence counts.
- Testing Reality angle-resolved polarizer coincidence data.
- Glasgow pixel-super-resolution raw figure data for Type-I BBO spatial
  photon-pair measurements.

The ideal but currently missing public dataset would be a simple Type-I BBO
phase-matching angle scan with:

```csv
theta_deg,pump_power_mw,integration_time_s,signal_counts,idler_counts,coincidence_counts,accidental_counts
```

If such a dataset is not found, do not invent it. Use the public datasets above
and clearly state that phase-matching is validated indirectly.

2. Decide the validation metric.

Good options:

- normalized residuals between experiment and simulation
- root-mean-square error (RMSE)
- coefficient of determination (`R^2`)
- fitted angular offset between simulated and measured peaks
- fitted brightness/coupling scale factor

3. Add experimental uncertainty.

Coincidence counts are count data, so a first uncertainty model can use Poisson
statistics:

```text
sigma_N ~= sqrt(N)
```

If accidental counts are measured, subtract them and propagate their uncertainty.

## Code Gaps

- Add optional uncertainty columns to `compare`.
- Add a theta-scan plotting mode with error bars if a public angle-scan table is found.
- Add a real ring-image comparison once a clean public experimental ring matrix is found
  or digitized from an acceptable source.
- Add a wavelength-scan comparison if the experimental data is spectral rather
  than angular.
- Add a small Methods notebook or script that reproduces every thesis figure in
  one command.
- Add richer metadata to configuration files: crystal cut angle, detector
  distance, filter bandwidth, detector efficiency, and coincidence window.

## Writing Gaps

- Methods section: describe package structure, numerical equations, parameter
  choices, and data preprocessing.
- Results section: include phase-matching report, `sinc^2` graph, walk-off graph,
  theta-tuning graph, and experiment-vs-simulation residual plot.
- Discussion section: explain why a scale factor is expected in count-rate
  comparisons due to detector efficiency, coupling loss, filter bandwidth, and
  alignment.
- Limitations section: make clear that public validation data replace an
  in-house thesis measurement.
