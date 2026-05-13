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
bbo-spdc compare-polarization \
  --polarization-data data/external/testing_reality_entanglement/data_allAngles.csv \
  --out outputs/compare_polarization_testing_reality
```
