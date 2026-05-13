# Athleity/SPDC_Project Data Notes

Source repo: <https://github.com/Athleity/SPDC_Project>

Imported files:

- `BBO_data.csv`: BBO ordinary/extraordinary refractive-index table. This is useful as a quick external reference table, not as theta-scan count data.
- `fit_data.csv`: pump power vs coincidence-rate sample/proxy data with source fit and residual columns. The source script labels these values as sample data to replace with real lab measurements, so do not cite it as your own experimental result.
- `thesis_ecmbi_per_file_summary.csv`: tomography-derived per-file summary with power, state, HH/HV/VH/VV counts, fidelity and Bell-S estimate.
- `thesis_ecmbi_averaged_by_power.csv`: tomography summary averaged by power.

Important: these files are external reference/sample data. They are not a substitute for your own lab measurements, and they do not contain the same theta-scan columns expected by `data/experimental/experimental_counts.csv`. Use them to test the comparison workflow, not as final thesis evidence.

Run the imported power scan comparison:

```bash
bbo-spdc compare-power --power-scan data/external/athleity_spdc_project/fit_data.csv --out outputs/compare_power
```
