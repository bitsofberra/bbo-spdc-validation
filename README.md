# BBO Type-I SPDC Validation

Bu repo, BBO kristalinde Type-I SPDC icin simulasyon ciktilari uretmek ve deney verileriyle karsilastirmak icin hazirlanmis Python paketidir.

Amac:

- phase matching kosullarini hesaplamak
- sinc^2 faz eslesme grafigi uretmek
- pump walk-off etkisini gorsellestirmek
- farkli theta acilarinda halka/tepe konumunun ne kadar kaydigini gostermek
- dolanik foton/cakisma sayaci icin deneyle kalibre edilebilir tahmin uretmek

Fizik cekirdegi BBO Sellmeier denklemleri, extraordinary etkin indis, Type-I collinear/non-collinear faz uyumu ve `sinc^2(Delta k L / 2)` modelini kullanir. Daha agir 4 boyutlu momentum integrali ileride eklenebilir; mevcut paket tezde ilk dogrulama ve deney karsilastirma akisini kurmak icindir.

## Kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Ilk demo

```bash
bbo-spdc run-demo --out outputs/demo
```

Bu komut sunlari uretir:

- `phase_matching_report.json`
- `phase_matching_summary.txt`
- `sinc2_phase_matching.png`
- `walkoff_effect.png`
- `theta_tuning_shift.png`
- `entangled_counter_demo.png`

## Deney verisi ekleme

Olcumleri [data/experimental/experimental_counts.csv](/Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez/data/experimental/experimental_counts.csv) dosyasina ekle.

Beklenen kolonlar:

```csv
theta_deg,pump_power_mw,integration_time_s,signal_counts,idler_counts,coincidence_counts
```

Sonra:

```bash
bbo-spdc compare --experimental data/experimental/experimental_counts.csv --out outputs/compare
```

Karsilastirma komutu deney coincidence sayimlarindan parlaklik katsayisini kalibre eder, simulasyon tahminlerini CSV olarak yazar ve deney/simulasyon grafigi uretir.

## Dis ornek/proxy veri

`Athleity/SPDC_Project` reposunda theta-scan deney verisi yok. Icindeki `fit_data.csv` de kaynak scriptte "sample data, replace with your actual lab measurements" olarak geciyor. Bu yuzden bu dosyayi tezde kendi deney verin gibi sunmamak gerekir.

Yine de ise yarar: kendi deney verin gelene kadar theory/koddan cikan simulasyonun power-vs-coincidence davranisini bir public ornek/proxy veri seti uzerinde test edebiliriz. BBO indis tablosu ve tomography ozetleri de [data/external/athleity_spdc_project](/Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez/data/external/athleity_spdc_project) altinda duruyor.

Power scan örneğini çalıştırmak için:

```bash
bbo-spdc compare-power --power-scan data/external/athleity_spdc_project/fit_data.csv --out outputs/compare_power
```

## VS Code ve GitHub

Adim adim kurulum notlari [docs/vscode_github_steps.md](/Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez/docs/vscode_github_steps.md) dosyasinda.

## Kaynak notu

Bu paket, referans olarak verilen `mvchalupnik/spdc-simulator` reposundaki BBO SPDC yaklasimini daha tez odakli, paketlenebilir ve deney verisiyle karsilastirilabilir hale getirir. Oradaki README, denklemlerin Suman Karan et al. 2020, J. Opt. 22 083501 calismasina dayandigini belirtiyor.
