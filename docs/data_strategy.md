# Data Strategy

This project separates theoretical simulation outputs, real public experimental
data, proxy/sample data, and future thesis measurements.

## 1. Theory and Simulation

These are values generated directly by the package from the thesis theory:

- BBO refractive indices from Sellmeier equations
- effective extraordinary pump index
- Type-I phase-matching condition
- phase mismatch `Delta k`
- `sinc^2(Delta k L / 2)` finite-crystal envelope
- non-collinear emission angle
- pump walk-off angle and lateral displacement
- predicted singles and coincidence counts

These outputs should be described in the thesis as theoretical or numerical
predictions.

## 2. Real Public Experimental Data

Two real BBO SPDC polarization datasets are now included:

- `data/external/testing_reality_entanglement/data_allAngles.csv`
- `data/external/epj_undergraduate_bell/phi_plus_table11.csv`

They are real BBO SPDC coincidence-count data, but they validate polarization
correlations rather than the BBO crystal-angle phase-matching curve.

Use them to develop and demonstrate the comparison workflow, especially the
connection between entangled-state theory and measured coincidence counts.

## 3. Proxy/Sample Data

`data/external/athleity_spdc_project/fit_data.csv` is not final experimental
evidence. The source script labels the values as sample data to be replaced by
actual lab measurements. Keep it as a software-test/proxy dataset only.

## 4. Future Thesis Measurements

The final thesis-specific dataset should be placed in:

`data/experimental/experimental_counts.csv`

Required columns:

```csv
theta_deg,pump_power_mw,integration_time_s,signal_counts,idler_counts,coincidence_counts
```

Recommended optional columns:

```csv
accidental_counts,coincidence_uncertainty,temperature_c,filter_center_nm,filter_bandwidth_nm,note
```

## Honest Reporting Language

Recommended wording for the current stage:

- "The theoretical SPDC outputs were generated using a Python package developed
  for this thesis."
- "The comparison workflow was tested using public BBO SPDC polarization
  coincidence datasets."
- "The final validation of the BBO phase-matching simulation requires a
  thesis-specific crystal-angle or wavelength-scan dataset."
