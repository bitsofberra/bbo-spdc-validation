# Data Strategy

This project separates theoretical simulation outputs, real public experimental
data, and proxy/sample data.

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

Four real BBO SPDC data sources are now included:

- `data/external/testing_reality_entanglement/data_allAngles.csv`
- `data/external/epj_undergraduate_bell/phi_plus_table11.csv`
- `data/external/glasgow_pixel_superresolution/Pixelsuperresolution.zip`
- `data/external/josa_b_elliptical_rings/bbo_eccentricity_table1.csv`

They are real BBO SPDC experimental data, but they do not all validate the same
part of the theory:

- Testing Reality validates polarization-angle coincidence behavior.
- EPJ Quantum Technology validates BBO Bell-state coincidence and tomography
  measurements, and also contains a manuscript figure for BBO alignment/angle
  optimization.
- Glasgow pixel-super-resolution validates Type-I BBO spatial photon-pair data
  from a published EMCCD experiment, as qualitative spatial context.
- JOSA B reports a near-zero BBO ring eccentricity used as literature context
  for the simulated circular Type-I ring.

Use these as the thesis experimental basis unless a better public BBO
phase-matching angle-scan dataset is found.

## 3. Literature Templates

- `data/external/karan_bbo_phase_matching/type1_theta_emccd_digitized.csv`
  contains published theta locations, while ring-radius fields remain blank.
- `data/external/byu_noncollinear_spdc/byu_fig3_3_digitized.csv` is an empty
  supplementary template for values entered by a documented digitization.

Numerical validation metrics are generated only after measurement values are
present. Karan theta markers alone do not support an RMSE or an R² statement.

## 4. Proxy/Sample Data

`data/external/athleity_spdc_project/fit_data.csv` is not final experimental
evidence. The source script labels the values as sample data to be replaced by
actual lab measurements. Keep it as a software-test/proxy dataset only.

## Honest Reporting Language

Recommended wording:

- "The theoretical SPDC outputs were generated using a Python package developed
  for this thesis."
- "Because no in-house experimental setup was available, validation was carried
  out using public experimental BBO SPDC datasets."
- "The public datasets validate polarization coincidence behavior and spatial
  photon-pair measurements; direct validation of the crystal-angle
  phase-matching curve is limited by public data availability."
- "The phase-matching, `sinc^2`, and walk-off figures should therefore be
  presented as theory-driven simulation outputs, while the public data are used
  to test the measurement-comparison workflow."
- "R²-based agreement is reported only for experimental polarization fits;
  theory-only figures carry no experimental agreement metric."
