from bbo_spdc.data_io import read_power_scan_csv


def test_read_power_scan_accepts_comment_header(tmp_path):
    path = tmp_path / "power.csv"
    path.write_text(
        "# Pump_power_mW,Coincidence_Hz,Coincidence_error_Hz\n"
        "50,0.05,0.02\n",
        encoding="utf-8",
    )

    rows = read_power_scan_csv(path)

    assert rows[0]["Pump_power_mW"] == "50"
    assert rows[0]["Coincidence_Hz"] == "0.05"
