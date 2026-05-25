from __future__ import annotations

import zipfile

from bbo_spdc.data_loaders import (
    load_epj_phi_plus_table11,
    load_glasgow_spatial_matrices,
)

def test_epj_loader_exposes_paper_count_columns():
    rows = load_epj_phi_plus_table11()

    assert rows
    assert {"alpha_deg", "beta_deg", "Na", "Nb", "Nc", "Nacc"}.issubset(rows[0])


def test_spatial_loader_skips_non_numeric_and_small_text_files(tmp_path):
    archive = tmp_path / "spatial.zip"
    numeric_line = ",".join(["1"] * 20)
    bright_line = ",".join(["2"] * 20)
    numeric_matrix = "\n".join([numeric_line] * 19 + [bright_line])
    with zipfile.ZipFile(archive, "w") as handle:
        handle.writestr("valid.txt", numeric_matrix)
        handle.writestr("words.txt", "not,a,numeric,matrix")
        handle.writestr("small.txt", "1,2\n3,4\n")

    matrices = load_glasgow_spatial_matrices(archive)

    assert len(matrices) == 1
    assert matrices[0][0] == "valid.txt"
