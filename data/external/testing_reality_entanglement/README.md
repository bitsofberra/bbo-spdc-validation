# Testing Reality Entanglement Dataset

Source: <https://testing-reality.webflow.io/experiment-4>

This is a real laboratory polarizer-angle scan from a BBO SPDC entanglement setup.
The source describes a 404 nm diode laser, two thin BBO crystals placed at 90 degrees,
rotatable polarizers in both output arms, SPAD detectors, and a coincidence-counting
system.

Imported file:

- `data_allAngles.csv`

Columns:

- `PolA`: polarizer angle in arm A, degrees
- `PolB`: polarizer angle in arm B, degrees
- `CountsA`: singles count at detector A
- `CountsB`: singles count at detector B
- `CountsAB`: two-detector coincidence count

The first line of the CSV states that each acquisition lasted 1 second with a
10 ns coincidence window.

Use:

```bash
bbo-spdc validate-polarization --dataset testing_reality --out outputs/polarization_testing
```

This is retained as a non-ideal experimental validation dataset because the
recorded coincidence map is imbalanced. The validation output reports
R²-based agreement and RMSE without treating it as an ideal source.
