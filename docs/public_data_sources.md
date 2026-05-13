# Public Experimental Data Sources

This thesis has no in-house experimental setup. The experimental side should
therefore be built from public, citable BBO SPDC datasets.

## Included and Usable Now

| Source | Local file | What it validates | Notes |
| --- | --- | --- | --- |
| Testing Reality, "Entanglement and polarizers" | `data/external/testing_reality_entanglement/data_allAngles.csv` | Bell-state coincidence vs polarizer angle | Real BBO/SPDC public CSV; fit already implemented. |
| EPJ Quantum Technology undergraduate Bell setup | `data/external/epj_undergraduate_bell/phi_plus_table11.csv` | Bell-state coincidence counts and tomography workflow | Real published table; fit already implemented. |
| University of Glasgow pixel-super-resolution dataset | `data/external/glasgow_pixel_superresolution/Pixelsuperresolution.zip` | Type-I BBO spatial photon-pair measurements | Real raw figure data; summarized with `bbo-spdc summarize-spatial`. |

## Closest Phase-Matching Leads

| Source | Status | Use in thesis |
| --- | --- | --- |
| EPJ Quantum Technology Fig. 9 and Sect. 4.4 | Data is provided in the manuscript, but not as a clean CSV | Can be used as a reference for the BBO alignment and angle-optimization discussion. |
| Karan et al., "Phase matching in BBO crystals for SPDC" | Strong phase-matching reference with experimental/numerical figures; no raw CSV found | Best theory reference for the phase-matching section. |
| Davenport et al., "Quantum ghost imaging microscopy depth-of-field study" | Very relevant Type-I BBO angle/length study, but Optica says data are not public at this time | Cite as related work; do not use as raw data unless authors provide it. |

## Ring and Walk-Off Figure Leads

| Source | Status | Use in thesis |
| --- | --- | --- |
| Defienne et al., "Pixel super-resolution with spatially entangled photons" | Included data archive has text matrices and figure data; the paper uses 405 nm Type-I BBO and 810 +/- 5 nm photon pairs | Use the included Glasgow archive as real spatial/camera evidence. It is not a clean free-space ring scan, because their setup deliberately works near-collinear for imaging. |
| Guilbert, Wong, and Gauthier, "Observation of elliptical rings in type-I spontaneous parametric downconversion" | Publisher preview shows BBO/BiBO ring camera images and experimental geometry; no raw downloadable matrix found | Good visual/reference source for the ring shape. |
| Durak, "Optimization of collection optics for maximum fidelity in entangled photon sources" | Open-access BBO/SPDC collection-optics and distinguishability paper; compares numerical simulation with experimental fidelity data | Good citation for why emission angle, collection optics, and walk-off-like spatial distinguishability matter. It is not a raw ring-image dataset. |
| Takeno et al., "Superresolution concentration measurement realized by sub-shot-noise absorption spectroscopy" | Open-access Type-I BBO paper with a published ring-shaped emission pattern in Fig. 2a | Good visual citation for ring emission from Type-I phase matching. No raw image matrix was found in the article page. |

## Not Final Experimental Evidence

`Athleity/SPDC_Project` is useful as code inspiration and software-test data, but
its `fit_data.csv` is sample data in the source script. Do not present it as real
experimental evidence.
