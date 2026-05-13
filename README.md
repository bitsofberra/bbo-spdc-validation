# BBO Type-I SPDC Simulation and Validation

This repository contains a Python package for modelling Type-I spontaneous
parametric down-conversion (SPDC) in beta-barium borate (BBO) crystals and for
comparing theory-driven simulation outputs with experimental coincidence-count
data.

The project follows the theory structure of the thesis draft, **"Numerical
Modeling and Validation of Type-1 Spontaneous Parametric Down-Conversion"**.
The current implementation focuses on the theoretical and numerical core. The
methods and results sections can be expanded once the final experimental
dataset is selected or measured.

## Thesis Motivation

SPDC is a second-order nonlinear optical process in which one pump photon is
converted inside a nonlinear crystal into two lower-energy photons, usually
called signal and idler. In a BBO Type-I configuration, the pump is treated as an
extraordinary wave, while the generated photons are ordinary waves with the same
polarization. The emission geometry and photon-pair yield are controlled by
energy conservation, momentum conservation, BBO birefringence, finite crystal
length, pump geometry, and detector collection.

This package turns those theory blocks into reproducible numerical outputs:

- phase-matching angle and phase mismatch
- BBO ordinary and extraordinary refractive indices from Sellmeier equations
- `sinc^2(Delta k L / 2)` phase-matching envelope
- angular acceptance around the degenerate wavelength
- non-collinear emission/ring-angle shift as the crystal angle changes
- spatial walk-off and its effect on collection overlap
- phenomenological photon-pair and coincidence-count predictions
- polarization-entanglement comparison against real BBO SPDC data

## Theory-to-Code Map

| Thesis topic | Code module | Output |
| --- | --- | --- |
| Quantum entanglement and nonlocality | `bbo_spdc.polarization` | Bell-state coincidence model |
| Gaussian pump and collection overlap | `bbo_spdc.counter` | pair-rate and walk-off overlap factor |
| SPDC energy and momentum conservation | `bbo_spdc.phase_matching` | `Delta k`, idler wavelength, emission angle |
| BBO birefringence | `bbo_spdc.sellmeier` | ordinary/extraordinary indices |
| Sellmeier equations for BBO | `bbo_spdc.sellmeier` | wavelength-dependent refractive index |
| Phase mismatch and `sinc^2` distribution | `bbo_spdc.phase_matching`, `bbo_spdc.plots` | phase-matching spectrum |
| Spatial walk-off | `bbo_spdc.sellmeier`, `bbo_spdc.plots` | walk-off angle and lateral shift |
| Detecting photon pairs | `bbo_spdc.counter`, `bbo_spdc.polarization` | singles/coincidence predictions |

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run the Baseline Simulation

```bash
bbo-spdc run-demo --out outputs/demo
```

This generates:

- `phase_matching_report.json`
- `phase_matching_summary.txt`
- `sinc2_phase_matching.png`
- `walkoff_effect.png`
- `theta_tuning_shift.png`
- `entangled_counter_demo.png`

For the default 405 nm pump and degenerate 810/810 nm signal-idler wavelengths,
the package currently finds a collinear Type-I BBO phase-matching angle of about
`28.67 deg`. The default demonstration angle is `28.95 deg`, so the output also
shows how a small angular detuning changes the non-collinear emission angle and
reduces the phase-matching strength.

## Experimental and External Data

The repository keeps three data categories separate.

### 1. Thesis/User Experimental Data

Your own final experimental data should go into:

[data/experimental/experimental_counts.csv](/Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez/data/experimental/experimental_counts.csv)

Expected columns:

```csv
theta_deg,pump_power_mw,integration_time_s,signal_counts,idler_counts,coincidence_counts
```

Run:

```bash
bbo-spdc compare --experimental data/experimental/experimental_counts.csv --out outputs/compare
```

This is the main route for the final thesis comparison between the simulation
and your own BBO angle-scan/counting measurements.

### 2. Real Public BBO SPDC Polarization Data

Two real experimental data sources were added for validating the comparison
workflow before your own measurements are available.

Testing Reality entanglement dataset:

- source: <https://testing-reality.webflow.io/experiment-4>
- setup: 404 nm laser, two thin BBO crystals, rotatable polarizers, SPAD
  detectors, 10 ns coincidence window
- file: `data/external/testing_reality_entanglement/data_allAngles.csv`
- result with the current model: balanced `Phi+` fit `R^2 = 0.467`, unbalanced
  correlated Bell-state fit `R^2 = 0.507`

```bash
bbo-spdc compare-polarization \
  --polarization-data data/external/testing_reality_entanglement/data_allAngles.csv \
  --out outputs/compare_polarization_testing_reality
```

EPJ Quantum Technology Bell-test dataset:

- source: <https://epjquantumtechnology.springeropen.com/articles/10.1140/epjqt/s40507-024-00298-y>
- setup: BBO-based undergraduate Bell-test/tomography source
- file: `data/external/epj_undergraduate_bell/phi_plus_table11.csv`
- result with the current model: balanced `Phi+` fit `R^2 = 0.912`, unbalanced
  correlated Bell-state fit `R^2 = 0.982`

```bash
bbo-spdc compare-polarization \
  --polarization-data data/external/epj_undergraduate_bell/phi_plus_table11.csv \
  --out outputs/compare_polarization_epj
```

### 3. Proxy/Sample Data

The `Athleity/SPDC_Project` repository includes useful BBO reference tables and
sample analysis files, but its `fit_data.csv` is marked in the source script as
sample data to replace with real measurements. It is therefore kept only as a
proxy dataset for checking the software pipeline, not as final experimental
evidence.

```bash
bbo-spdc compare-power \
  --power-scan data/external/athleity_spdc_project/fit_data.csv \
  --out outputs/compare_power
```

## Current Validation Status

Implemented and tested:

- BBO Sellmeier equations and effective extraordinary index
- Type-I collinear phase-matching angle search
- symmetric non-collinear emission-angle estimate
- `sinc^2` finite-crystal phase-matching envelope
- pump walk-off angle and lateral shift
- photon-pair counter model with dark counts and accidentals
- polarization coincidence model for `Phi+` and unbalanced correlated states
- CLI commands for reports, demos, power-scan comparisons, and polarization comparisons
- public real-data ingestion for BBO SPDC polarization measurements

Automated tests:

```bash
pytest
```

## Remaining Work

The next scientific gap is not code structure; it is data matching. The current
phase-matching simulation predicts BBO crystal-angle and wavelength behavior,
while the strongest public real datasets found so far are polarization-angle
coincidence measurements. For the final thesis, the most valuable missing
dataset would be a BBO Type-I angle scan with columns such as crystal angle,
pump power, integration time, singles counts, coincidence counts, and optionally
accidental coincidences.

See [docs/remaining_work.md](/Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez/docs/remaining_work.md) for a focused checklist.

## VS Code and GitHub

Setup notes are in:

[docs/vscode_github_steps.md](/Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez/docs/vscode_github_steps.md)

## References and Code Inspiration

The package was inspired by the structure and physics focus of:

- <https://github.com/mvchalupnik/spdc-simulator>
- <https://github.com/Athleity/SPDC_Project>

The first repository is mainly a simulation reference. The second contains
sample/proxy files and some BBO-related tabular outputs. Neither replaces the
need for a final thesis-specific experimental dataset.
