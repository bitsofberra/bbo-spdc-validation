"""Helpers for public SPDC spatial image/matrix datasets."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np


@dataclass(frozen=True)
class SpatialMatrixSummary:
    """Compact metadata for one real experimental matrix."""

    name: str
    rows: int
    columns: int
    minimum: float
    maximum: float
    mean: float
    total: float

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "rows": self.rows,
            "columns": self.columns,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "mean": self.mean,
            "total": self.total,
        }


def read_zip_text_matrices(zip_path: str | Path) -> list[tuple[str, np.ndarray]]:
    """Read comma-separated text matrices from a public raw-data zip archive."""

    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(zip_path)

    matrices: list[tuple[str, np.ndarray]] = []
    with ZipFile(zip_path) as archive:
        for name in sorted(archive.namelist()):
            if not name.lower().endswith(".txt") or Path(name).name.lower().startswith("readme"):
                continue
            data = archive.read(name)
            matrix = np.loadtxt(BytesIO(data), delimiter=",")
            if matrix.ndim == 1:
                matrix = matrix.reshape(1, -1)
            matrices.append((name, matrix))
    return matrices


def summarize_matrices(matrices: list[tuple[str, np.ndarray]]) -> list[SpatialMatrixSummary]:
    """Summarize real experimental image matrices for reporting."""

    summaries = []
    for name, matrix in matrices:
        summaries.append(
            SpatialMatrixSummary(
                name=name,
                rows=int(matrix.shape[0]),
                columns=int(matrix.shape[1]),
                minimum=float(np.nanmin(matrix)),
                maximum=float(np.nanmax(matrix)),
                mean=float(np.nanmean(matrix)),
                total=float(np.nansum(matrix)),
            )
        )
    return summaries


def write_spatial_summary_csv(
    path: str | Path, summaries: list[SpatialMatrixSummary]
) -> None:
    """Write matrix summaries to CSV."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["name", "rows", "columns", "minimum", "maximum", "mean", "total"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            writer.writerow(summary.as_dict())
