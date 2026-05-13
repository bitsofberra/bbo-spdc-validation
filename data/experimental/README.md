# Optional Experimental Data

This folder is optional. If a supervisor later provides a small experimental
table, place it in `experimental_counts.csv`.

Required columns:

- `theta_deg`: BBO/pump phase-matching angle, degrees
- `pump_power_mw`: pump power, mW
- `integration_time_s`: counting/integration time, seconds
- `signal_counts`: signal dedektor toplam sayimi
- `idler_counts`: idler dedektor toplam sayimi
- `coincidence_counts`: coincidence/dolanik foton cifti sayimi

Optional columns:

- `coincidence_uncertainty`
- `accidental_counts`
- `note`
