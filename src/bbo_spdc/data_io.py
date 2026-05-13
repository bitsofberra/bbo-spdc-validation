"""CSV and JSON IO helpers."""

from __future__ import annotations

import csv
import json
from io import StringIO
from pathlib import Path


REQUIRED_EXPERIMENTAL_COLUMNS = {
    "theta_deg",
    "pump_power_mw",
    "integration_time_s",
    "signal_counts",
    "idler_counts",
    "coincidence_counts",
}

REQUIRED_POWER_SCAN_COLUMNS = {
    "Pump_power_mW",
    "Coincidence_Hz",
}


def read_experimental_csv(path: str | Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    clean_lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not clean_lines:
        return []
    reader = csv.DictReader(StringIO("\n".join(clean_lines)))
    if reader.fieldnames is None:
        return []
    missing = REQUIRED_EXPERIMENTAL_COLUMNS.difference(reader.fieldnames)
    if missing:
        raise ValueError(f"Missing experimental CSV columns: {sorted(missing)}")
    rows = []
    for row in reader:
        if not any((value or "").strip() for value in row.values()):
            continue
        rows.append(row)
    return rows


def read_power_scan_csv(path: str | Path) -> list[dict]:
    """Read pump-power vs coincidence data.

    Some imported datasets prefix the header line with "#". This reader keeps
    comment-style metadata out while still accepting that common header format.
    """

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    lines = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#") and not lines:
            line = line.lstrip("#").strip()
        elif line.startswith("#"):
            continue
        lines.append(line)
    if not lines:
        return []
    reader = csv.DictReader(StringIO("\n".join(lines)))
    if reader.fieldnames is None:
        return []
    missing = REQUIRED_POWER_SCAN_COLUMNS.difference(reader.fieldnames)
    if missing:
        raise ValueError(f"Missing power-scan CSV columns: {sorted(missing)}")
    return [row for row in reader]


def write_json(path: str | Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: str | Path, rows: list[dict]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_phase_matching_summary(path: str | Path, report: dict) -> None:
    phase = report["phase_matching"]
    walkoff = report["walkoff"]
    indices = report["indices"]
    text = "\n".join(
        [
            "BBO Type-I SPDC phase matching summary",
            "",
            f"Collinear theta: {phase['theta_collinear_deg']:.6f} deg",
            f"Current Delta k: {phase['delta_k_current_rad_per_m']:.6e} rad/m",
            f"Current sinc^2: {phase['sinc2_current']:.6f}",
            f"Coherence length: {phase['coherence_length_current_mm']:.6f} mm",
            f"Internal emission angle: {phase['internal_emission_angle_deg']:.6f} deg",
            f"External emission angle: {phase['external_emission_angle_deg']:.6f} deg",
            "",
            f"Pump n_o: {indices['pump_n_o']:.6f}",
            f"Pump n_e: {indices['pump_n_e']:.6f}",
            f"Pump n_eff(theta): {indices['pump_n_eff_at_theta']:.6f}",
            f"Signal n_o: {indices['signal_n_o']:.6f}",
            "",
            f"Walk-off rho: {walkoff['rho_mrad']:.6f} mrad",
            f"Walk-off lateral shift: {walkoff['lateral_shift_um']:.6f} um",
            f"Shift / pump waist: {walkoff['shift_over_pump_waist']:.6f}",
        ]
    )
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
