from __future__ import annotations

import zipfile

import numpy as np

from bbo_spdc.spatial_data import read_zip_text_matrices, summarize_matrices


def test_read_zip_text_matrices(tmp_path):
    archive = tmp_path / "matrices.zip"
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("Figure1a.txt", "1,2,3\n4,5,6\n")
        handle.writestr("Readme.txt", "ignore me")

    matrices = read_zip_text_matrices(archive)

    assert len(matrices) == 1
    assert matrices[0][0] == "Figure1a.txt"
    np.testing.assert_allclose(matrices[0][1], [[1, 2, 3], [4, 5, 6]])


def test_summarize_matrices():
    summaries = summarize_matrices([("example.txt", np.array([[1.0, 2.0], [3.0, 4.0]]))])

    assert summaries[0].as_dict() == {
        "name": "example.txt",
        "rows": 2,
        "columns": 2,
        "minimum": 1.0,
        "maximum": 4.0,
        "mean": 2.5,
        "total": 10.0,
    }
