# Optional Experimental Data

This folder is reserved for local experimental count tables that should not be
included in public validation unless explicitly intended.

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
