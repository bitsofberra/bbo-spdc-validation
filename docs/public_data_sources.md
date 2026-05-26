# Public Experimental Data Sources

This thesis has no in-house experimental setup. The experimental side should
therefore be built from public, citable BBO SPDC datasets.

## Included and Usable Now

| Source | Local file | What it validates | Notes |
| --- | --- | --- | --- |
| Testing Reality, "Entanglement and polarizers" | `data/external/testing_reality_entanglement/data_allAngles.csv` | Bell-state coincidence vs polarizer angle | Real BBO/SPDC public CSV; fit already implemented. |
| EPJ Quantum Technology undergraduate Bell setup | `data/external/epj_undergraduate_bell/phi_plus_table11.csv` | Bell-state coincidence counts and tomography workflow | Real published table; fit already implemented. |
| University of Glasgow pixel-super-resolution dataset | `data/external/glasgow_pixel_superresolution/Pixelsuperresolution.zip` | Type-I BBO spatial photon-pair measurements | Real raw figure data; used as qualitative spatial context, not a calibrated ring scan. |
| Guilbert, Wong, and Gauthier, JOSA B Table 1 | `data/external/josa_b_elliptical_rings/bbo_eccentricity_table1.csv` | Near-circular Type-I BBO ring eccentricity | Reported literature table value. |

## Theta and Ring Templates

| Source | Local file | Status | Use in thesis |
| --- | --- | --- | --- |
| Karan et al., "Phase matching in BBO crystals for SPDC" | `data/external/karan_bbo_phase_matching/type1_theta_emccd_digitized.csv` | Annular radii from Figure 8(b,c,e,f) digitized in `figure_px`; `28.64 deg` is a central blob without assigned annular radius | Main theta/ring figure reports paper-internal RMSE/MAE in pixels; it is not a calibrated package-model fit. |
| BYU thesis, "Numerical Model of Non-collinear SPDC" | `data/external/byu_noncollinear_spdc/byu_fig3_3_digitized.csv` | Empty digitization template | Supplementary comparison only because wavelengths differ from the default configuration. |

## Not Final Experimental Evidence

`Athleity/SPDC_Project` is useful as code inspiration and software-test data, but
its `fit_data.csv` is sample data in the source script. Do not present it as real
experimental evidence.
