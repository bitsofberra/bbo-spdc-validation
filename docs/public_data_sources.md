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
| EPJ Quantum Technology Fig. 9 and Sect. 4.4 | Data is provided in the manuscript, but not as a clean CSV | Can be digitized or manually transcribed if the supervisor accepts figure-derived data. |
| Karan et al., "Phase matching in BBO crystals for SPDC" | Strong phase-matching reference with experimental/numerical figures; no raw CSV found | Best theory reference for the phase-matching section. |
| Davenport et al., "Quantum ghost imaging microscopy depth-of-field study" | Very relevant Type-I BBO angle/length study, but Optica says data are not public at this time | Cite as related work; do not use as raw data unless authors provide it. |

## Not Final Experimental Evidence

`Athleity/SPDC_Project` is useful as code inspiration and software-test data, but
its `fit_data.csv` is sample data in the source script. Do not present it as real
experimental evidence.
