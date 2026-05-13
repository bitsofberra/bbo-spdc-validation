# Data Strategy

Bu projede uc farkli veri turunu ayri tutuyoruz:

1. `Theory / simulation`

Kodun BBO Sellmeier denklemleri, effective extraordinary index, phase matching, walk-off ve sayac modeliyle urettiği veridir. Bu kisim tezde "simulation/theoretical prediction" olarak anlatilacak.

2. `External sample/proxy data`

[data/external/athleity_spdc_project](/Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez/data/external/athleity_spdc_project) altindaki dosyalardir. Bunlar public repodan alindi. `fit_data.csv` kaynak scriptte sample lab data olarak geciyor; bu yuzden final deney sonucu gibi kullanilmaz. Amaci, bizim karsilastirma pipeline'imizin calistigini gostermek ve gercek veri gelene kadar prova yapmaktir.

3. `Your experimental data`

Sen kendi olcumlerini aldiginda [data/experimental/experimental_counts.csv](/Users/smyybrr/Documents/Codex/2026-05-13/files-mentioned-by-the-user-tez/data/experimental/experimental_counts.csv) dosyasina koyacagiz. Tezde asil "experiment vs simulation" karsilastirmasi bu dosya ile yapilacak.

Su an yapabilecegimiz en durust raporlama:

- "Simulation/theory outputs were generated using the package."
- "The comparison workflow was tested using a public sample/proxy dataset."
- "Final experimental validation will be performed after lab measurements are inserted."
