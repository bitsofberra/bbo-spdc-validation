# EPJ Quantum Technology Bell-Test Dataset

Source: Raul Lahoz Sanz et al., "Undergraduate setup for measuring the Bell
inequalities and performing quantum state tomography", EPJ Quantum Technology
11, 86 (2024).

Article: <https://epjquantumtechnology.springeropen.com/articles/10.1140/epjqt/s40507-024-00298-y>

Imported file:

- `phi_plus_table11.csv`

The CSV is transcribed from Table 11, which reports data obtained with the setup
shown in the article's Fig. 4 for the `|Phi+>` Bell state. Each measurement lasts
30 seconds. Columns include polarizer angles, singles counts, measured
coincidences, and averaged accidental coincidences.

Use:

```bash
bbo-spdc compare-polarization \
  --polarization-data data/external/epj_undergraduate_bell/phi_plus_table11.csv \
  --out outputs/compare_polarization_epj
```
