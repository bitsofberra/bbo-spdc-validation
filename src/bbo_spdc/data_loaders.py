"""Load public and digitized literature datasets used for validation."""

from __future__ import annotations

import csv
from io import BytesIO, StringIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

import numpy as np


DEFAULT_EPJ_PATH = "data/external/epj_undergraduate_bell/phi_plus_table11.csv"
DEFAULT_TESTING_REALITY_PATH = (
    "data/external/testing_reality_entanglement/data_allAngles.csv"
)
DEFAULT_KARAN_PATH = (
    "data/external/karan_bbo_phase_matching/type1_theta_emccd_digitized.csv"
)
DEFAULT_BYU_PATH = "data/external/byu_noncollinear_spdc/byu_fig3_3_digitized.csv"
DEFAULT_JOSA_PATH = "data/external/josa_b_elliptical_rings/bbo_eccentricity_table1.csv"
DEFAULT_GLASGOW_PATH = (
    "data/external/glasgow_pixel_superresolution/Pixelsuperresolution.zip"
)


def _clean_csv_rows(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    lines = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not lines:
        return []
    return list(csv.DictReader(StringIO("\n".join(lines))))


def _float(value, default: float = float("nan")) -> float:
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _bool(value) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "digitized"}


def load_epj_phi_plus_table11(path: str | Path = DEFAULT_EPJ_PATH) -> list[dict]:
    """Load EPJ Table 11 and expose the paper's Na/Nb/Nc/Nacc notation."""

    rows = []
    for row in _clean_csv_rows(path):
        rows.append(
            {
                "alpha_deg": _float(row.get("alpha_deg")),
                "beta_deg": _float(row.get("beta_deg")),
                "Na": _float(row.get("Na", row.get("signal_counts"))),
                "Nb": _float(row.get("Nb", row.get("idler_counts"))),
                "Nc": _float(row.get("Nc", row.get("coincidence_counts"))),
                "Nacc": _float(row.get("Nacc", row.get("accidental_counts")), 0.0),
                "integration_time_s": _float(row.get("integration_time_s")),
                "source_table": row.get("source_table", "Table 11"),
            }
        )
    return rows


def load_testing_reality_all_angles(
    path: str | Path = DEFAULT_TESTING_REALITY_PATH,
) -> list[dict]:
    """Load one-second Testing Reality polarizer coincidence measurements."""

    rows = []
    for row in _clean_csv_rows(path):
        rows.append(
            {
                "alpha_deg": _float(row.get("PolA", row.get("alpha_deg"))),
                "beta_deg": _float(row.get("PolB", row.get("beta_deg"))),
                "Na": _float(row.get("CountsA", row.get("signal_counts"))),
                "Nb": _float(row.get("CountsB", row.get("idler_counts"))),
                "Nc": _float(row.get("CountsAB", row.get("coincidence_counts"))),
                "Nacc": _float(row.get("Nacc", row.get("accidental_counts")), 0.0),
                "integration_time_s": 1.0,
            }
        )
    return rows


def load_karan_theta_digitized(path: str | Path = DEFAULT_KARAN_PATH) -> list[dict]:
    """Load Karan et al. theta markers and optional digitized ring radii."""

    rows = []
    for row in _clean_csv_rows(path):
        rows.append(
            {
                "source": row.get("source", ""),
                "figure": row.get("figure", ""),
                "theta_p_deg": _float(row.get("theta_p_deg")),
                "experimental_ring_radius_mm_or_px": _float(
                    row.get("experimental_ring_radius_mm_or_px")
                ),
                "experimental_ring_radius_uncertainty": _float(
                    row.get("experimental_ring_radius_uncertainty")
                ),
                "model_ring_radius_mm_or_px": _float(
                    row.get("model_ring_radius_mm_or_px")
                ),
                "notes": row.get("notes", ""),
                "digitized": _bool(row.get("digitized", "")),
            }
        )
    return rows


def load_byu_digitized(path: str | Path = DEFAULT_BYU_PATH) -> list[dict]:
    """Load optional digitized BYU non-collinear ring-diameter values."""

    fields = [
        "pump_nm",
        "daughter_nm",
        "crystal_angle_face_deg",
        "crystal_angle_axis_deg",
        "observed_ring_diameter_no_lens_deg",
        "observed_ring_diameter_with_lens_deg",
        "model_ring_diameter_deg",
        "observed_ring_width_no_lens_deg",
        "observed_ring_width_with_lens_deg",
        "model_ring_width_deg",
        "fractional_signal_no_lens",
        "fractional_signal_with_lens",
    ]
    rows = []
    for row in _clean_csv_rows(path):
        parsed = {
            "source": row.get("source", ""),
            "figure": row.get("figure", ""),
            "notes": row.get("notes", ""),
            "digitized": _bool(row.get("digitized", "")),
        }
        parsed.update({field: _float(row.get(field)) for field in fields})
        rows.append(parsed)
    return rows


def load_josa_b_eccentricity(path: str | Path = DEFAULT_JOSA_PATH) -> list[dict]:
    """Load reported JOSA B Type-I BBO ring eccentricity values."""

    rows = []
    for row in _clean_csv_rows(path):
        rows.append(
            {
                "crystal": row.get("crystal", ""),
                "experiment_eccentricity": _float(row.get("experiment_eccentricity")),
                "theory_eccentricity": _float(row.get("theory_eccentricity")),
                "statistical_error": _float(row.get("statistical_error")),
                "systematic_error": _float(row.get("systematic_error")),
                "source": row.get("source", ""),
            }
        )
    return rows


def load_glasgow_spatial_matrices(
    zip_path: str | Path = DEFAULT_GLASGOW_PATH,
    minimum_pixels: int = 20,
) -> list[tuple[str, np.ndarray]]:
    """Read usable numeric 2D matrices from the Glasgow public archive."""

    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(zip_path)
    matrices = []
    try:
        with ZipFile(zip_path) as archive:
            for name in sorted(archive.namelist()):
                if not name.lower().endswith(".txt"):
                    continue
                if Path(name).name.lower().startswith("readme"):
                    continue
                try:
                    matrix = np.loadtxt(BytesIO(archive.read(name)), delimiter=",")
                except (OSError, UnicodeError, ValueError):
                    continue
                if matrix.ndim != 2:
                    continue
                if min(matrix.shape) < minimum_pixels or not np.isfinite(matrix).any():
                    continue
                if float(np.nanmax(matrix) - np.nanmin(matrix)) <= 0.0:
                    continue
                matrices.append((name, np.asarray(matrix, dtype=float)))
    except BadZipFile:
        return []
    return matrices
