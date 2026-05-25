# BBO Type-I SPDC Simulation and Validation

This repository contains a Python package for modelling Type-I spontaneous
parametric down-conversion (SPDC) in beta-barium borate (BBO) crystals and for
comparing theory-driven simulation outputs with experimental coincidence-count
data.

The project follows the theory structure of the thesis draft, **"Numerical
Modeling and Validation of Type-I Spontaneous Parametric Down-Conversion"**.
The current implementation focuses on the theoretical and numerical core. Since
an in-house experiment is not available, the validation part of the thesis is
designed around public experimental datasets from published BBO SPDC
experiments.

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
- simulated far-field SPDC ring image
- spatial walk-off and its effect on collection overlap
- phenomenological photon-pair and coincidence-count predictions
- polarization-entanglement comparison against real BBO SPDC data

## Theory-to-Code Map

| Thesis topic | Code module | Output |
| --- | --- | --- |
| Quantum entanglement and nonlocality | `bbo_spdc.polarization_validation` | Bell-state model vs experimental coincidences |
| Gaussian pump and collection overlap | `bbo_spdc.counter` | pair-rate and walk-off overlap factor |
| SPDC energy and momentum conservation | `bbo_spdc.phase_matching` | `Delta k`, idler wavelength, emission angle |
| BBO birefringence | `bbo_spdc.sellmeier` | ordinary/extraordinary indices |
| Sellmeier equations for BBO | `bbo_spdc.sellmeier` | wavelength-dependent refractive index |
| Phase mismatch and `sinc^2` distribution | `bbo_spdc.phase_matching`, `bbo_spdc.plots` | phase-matching spectrum |
| Non-collinear emission ring | `bbo_spdc.ring`, `bbo_spdc.theta_validation` | theta/ring literature-linked figure |
| Spatial imaging and ring shape | `bbo_spdc.spatial_validation` | qualitative spatial comparison and eccentricity summary |
| Spatial walk-off | `bbo_spdc.sellmeier`, `bbo_spdc.plots` | supplementary theory-only figure |
| Detecting photon pairs | `bbo_spdc.counter`, `bbo_spdc.polarization` | singles/coincidence predictions |

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Clean Thesis Output Set

Generate the focused Results-section figures with:

```bash
bbo-spdc thesis-run --out outputs/thesis_run
```

The command creates these main figures:

| Figure | Theory topic | Dataset | Metric | Status |
| --- | --- | --- | --- | --- |
| `model_sinc2_phase_matching.png` | Phase mismatch and finite-crystal `sinc^2` envelope | None; numerical model | No experimental metric | Main |
| `theta_ring_validation.png` | Type-I phase matching and theta/ring tuning | Karan et al. theta markers; digitized radius template | RMSE/MAE only when radii are entered | Main |
| `polarization_validation_epj_phi_plus.png` | Polarization entanglement | EPJ Quantum Technology Table 11 | R²-based agreement; RMSE | Main |
| `polarization_validation_testing_reality.png` | Polarization coincidence behavior | Testing Reality public CSV | R²-based agreement; RMSE | Main |
| `spatial_ring_validation.png` | Spatial/ring geometry | Glasgow spatial matrices; JOSA B eccentricity context | Qualitative comparison | Main |
| `supplementary/walkoff_effect.png` | Gaussian overlap and walk-off | None; numerical model | No experimental metric | Supplementary |
| `supplementary/byu_ring_diameter_validation.png` | Non-collinear ring diameter | BYU digitized literature template | Offset-corrected RMSE when populated | Supplementary, conditional |
| `supplementary/spatial_eccentricity_summary.csv` | Type-I BBO ring circularity | JOSA B Table 1 | Reported eccentricity | Supplementary |

It also creates:

- `validation_summary.md`, `validation_summary.csv`, and `validation_summary.json`
- `figure_captions.md`
- `polarization_validation_epj_phi_plus.csv`

`R²-based agreement (%)` replaces the earlier fit-percentage wording and is
used only for real experimental polarization fits. Theory-only figures have no
experimental agreement value. The theta figure does not report an agreement
metric until traceable ring-radius values are added to the digitized literature
template.

## Experimental and External Data

The repository separates public experimental datasets from proxy/sample data.

### Included Real Data

```bash
bbo-spdc validate-polarization --dataset epj --out outputs/polarization_epj
bbo-spdc validate-polarization --dataset testing_reality --out outputs/polarization_testing
bbo-spdc validate-spatial --out outputs/spatial_validation
```

| Dataset | Local file | Validation use |
| --- | --- | --- |
| EPJ Quantum Technology Table 11 | `data/external/epj_undergraduate_bell/phi_plus_table11.csv` | Primary corrected-coincidence Bell-state fit using `Ncorr = Nc - Nacc` |
| Testing Reality | `data/external/testing_reality_entanglement/data_allAngles.csv` | Secondary non-ideal polarization validation |
| Glasgow pixel-super-resolution collection | `data/external/glasgow_pixel_superresolution/Pixelsuperresolution.zip` | Qualitative public spatial/camera comparison; not a calibrated free-space ring scan |
| JOSA B elliptical-rings Table 1 | `data/external/josa_b_elliptical_rings/bbo_eccentricity_table1.csv` | Published BBO near-circular ring eccentricity context |

### Digitized Literature Templates

```bash
bbo-spdc validate-theta --out outputs/theta_validation
```

| Source | Template | Current status |
| --- | --- | --- |
| Karan et al. Type-I BBO EMCCD images | `data/external/karan_bbo_phase_matching/type1_theta_emccd_digitized.csv` | Known theta values entered; radius values blank |
| BYU non-collinear SPDC thesis | `data/external/byu_noncollinear_spdc/byu_fig3_3_digitized.csv` | Empty template; supplementary only because wavelengths differ |

No numerical literature values are entered unless they are traceably reported
or digitized from a cited source.

## Current Validation Status

Implemented and tested:

- BBO Sellmeier equations and effective extraordinary index
- Type-I collinear phase-matching angle search
- symmetric non-collinear emission-angle estimate
- theta/ring curve with Karan literature theta markers and digitized-data loader
- `sinc^2` finite-crystal phase-matching envelope
- supplementary pump walk-off model
- corrected-coincidence polarization fits for balanced `Phi+` and unbalanced correlated states
- Glasgow spatial-matrix loading with qualitative profile visualization
- JOSA B eccentricity summary and optional BYU supplementary loader
- cleaned `thesis-run`, `validate-theta`, `validate-polarization`, and `validate-spatial` commands

Automated tests:

```bash
pytest
```

## References and Code Inspiration

Experimental and literature sources:

- Karan et al., "Phase matching in beta-barium borate crystals for spontaneous parametric down-conversion": <https://arxiv.org/abs/1810.01184>
- EPJ Quantum Technology Bell-test dataset: <https://epjquantumtechnology.springeropen.com/articles/10.1140/epjqt/s40507-024-00298-y>
- Testing Reality entanglement dataset: <https://testing-reality.webflow.io/experiment-4>
- Glasgow research data collection: <https://researchdata.gla.ac.uk/1269/>
- Guilbert, Wong, and Gauthier, JOSA B: <https://opg.optica.org/josab/abstract.cfm?uri=josab-32-10-2096>
- BYU thesis supplementary lead: <https://physics.byu.edu/docs/thesis/103>

Code inspiration:

- <https://github.com/mvchalupnik/spdc-simulator>
- <https://github.com/Athleity/SPDC_Project>

The first repository is mainly a simulation reference. The second contains
sample/proxy files and some BBO-related tabular outputs. Neither replaces the
need for clearly cited public experimental data.
