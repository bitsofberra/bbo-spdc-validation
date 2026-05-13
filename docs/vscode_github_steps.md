# VS Code ve GitHub Adimlari

## 1. Projeyi VS Code'da ac

```bash
cd /Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez
code .
```

VS Code `code` komutunu tanimiyorsa: VS Code icinde Command Palette ac, `Shell Command: Install 'code' command in PATH` sec.

## 2. Sanal ortam kur

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

VS Code sag altta Python yorumlayicisi olarak `.venv/bin/python` sec.

## 3. Demo ciktisini al

```bash
bbo-spdc run-demo --out outputs/demo
```

## 4. Deney CSV dosyasini doldur

`data/experimental/experimental_counts.csv` icine kendi olcumlerini ekle.

```csv
theta_deg,pump_power_mw,integration_time_s,signal_counts,idler_counts,coincidence_counts
28.64,10,1,12000,11800,820
28.74,10,1,14000,13950,1100
28.95,10,1,13100,13020,980
```

Sonra:

```bash
bbo-spdc compare --experimental data/experimental/experimental_counts.csv --out outputs/compare
```

## 5. GitHub reposuna bagla

Bu proje icin onerilen repo adi: `bbo-spdc-validation`.

GitHub'da `bitsofberra/bbo-spdc-validation` adli bos bir repo olustur. Sonra terminalde:

```bash
git init
git add .
git commit -m "Initial BBO SPDC validation package"
git branch -M main
git remote add origin https://github.com/bitsofberra/bbo-spdc-validation.git
git push -u origin main
```

GitHub CLI kullanmak istersen:

```bash
gh repo create REPO_ADIN --private --source . --remote origin --push
```
