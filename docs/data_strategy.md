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

## 3. Digitized Literature Data

- `data/external/karan_bbo_phase_matching/type1_theta_emccd_digitized.csv`
  contains digitized annular radial-peak radii from Karan et al. Figure 8 for
  `theta_p = 28.74 deg` and `28.95 deg`. Values are in `figure_px`, because
  the published image has no physical spatial scale. The `28.64 deg` central
  blob is retained without an assigned annular radius.
- `data/external/byu_noncollinear_spdc/byu_fig3_3_digitized.csv` is a
  supplementary dataset containing ten ring-diameter points digitized from
  Dustin Shipp's Figure 3.3: two observed CCD series and the published
  computational curve. It uses a `351 nm` pump and `690 +/- 5 nm` selected
  photons rather than the main `405 nm / 810 nm` configuration.

For Karan, RMSE and MAE compare the digitized experimental panels to the
corresponding numerical panels shown in the paper, in figure pixels. R² is not
reported from only two annular-radius points, and these pixel measurements are
not directly fitted to the package model's millimetre-scale curve.

For BYU, the supplementary metric compares digitized CCD observations to the
computational curve printed in the same thesis figure. An angular-offset fit
is permitted because there are ten literature points and the thesis explicitly
discusses a possible `0.2 deg` crystal-axis offset. The fitted comparison uses
linear extension at the digitized curve boundary, so it reports RMSE/MAE
rather than R². It must not be presented as direct validation of the package's
default-wavelength model.

## 4. Theory and Modeling References Without Raw Data

Christophe Couteau's 2018 SPDC review is useful for the theoretical discussion
of phase matching, BBO birefringence, `sinc^2` behavior, non-collinear cones,
and walk-off. It is not used as a Type-I validation dataset here.

The provided *Numerical Framework for Type-I SPDC Using Python* paper is
methodologically relevant, but its comparison table cites values from earlier
studies rather than supplying a new raw experimental dataset. It is therefore
not loaded as experimental validation data.

## 5. Proxy/Sample Data

`data/external/athleity_spdc_project/fit_data.csv` is not final experimental
evidence. The source script labels the values as sample data to be replaced by
actual lab measurements. Keep it as a software-test/proxy dataset only.

## Honest Reporting Language

Recommended wording:

- "The theoretical SPDC outputs were generated using a Python package developed
  for this thesis."
- "Because no in-house experimental setup was available, validation was carried
  out using public experimental BBO SPDC datasets."
- "Digitized Karan et al. Figure 8 data support a limited, paper-internal
  theta/ring comparison in figure pixels; a calibrated crystal-angle scan in
  physical units remains unavailable."
- "The phase-matching, `sinc^2`, and walk-off figures should therefore be
  presented as theory-driven simulation outputs, while the public data are used
  to test the measurement-comparison workflow."
- "R²-based agreement is reported only for experimental polarization fits;
  theory-only figures carry no experimental agreement metric."
