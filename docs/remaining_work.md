# Remaining Work

## Highest-Priority Scientific Gaps

1. Obtain a phase-matching dataset that matches the simulation.

The current simulation predicts how BBO crystal angle, wavelength, finite crystal
length, and walk-off affect Type-I SPDC. The most useful final dataset would
therefore contain:

```csv
theta_deg,pump_power_mw,integration_time_s,signal_counts,idler_counts,coincidence_counts,accidental_counts
```

If possible, keep pump power, filter bandwidth, detector position, and
integration time fixed while scanning the BBO angle.

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
- Add a theta-scan plotting mode with error bars once real angle-scan data is available.
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
- Limitations section: make clear which datasets are public validation data and
  which one is the final thesis-specific measurement.
