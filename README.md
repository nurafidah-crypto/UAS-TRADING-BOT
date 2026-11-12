# UAS Trading Bot — Indodax

## 1. Deskripsi Proyek

Proyek ini mengembangkan dan mengevaluasi sistem trading bot multi-pair untuk pasar aset kripto terhadap Rupiah (IDR) pada exchange Indodax.

Ruang lingkup penelitian meliputi:
- Pengumpulan dan validasi data historis.
- Perhitungan indikator teknikal.
- Backtesting multi-pair.
- Evaluasi out-of-sample (OOS).
- Analisis sensitivitas biaya transaksi.
- Perbandingan dengan benchmark Bitcoin.
- Forward testing dalam mode DRY_RUN.
- Pemantauan melalui dashboard lokal.

**Sistem ini merupakan prototipe penelitian dan simulasi. Sistem tidak dinyatakan siap untuk live trading.**

## 2. Teknologi

- Python
- Pandas dan NumPy
- Requests
- Indodax Public API
- HTML, CSS, dan JavaScript
- Git
- Windows Task Scheduler

## 3. Universe Pair

Pair yang digunakan dalam eksperimen:
- BTCIDR
- ETHIDR
- XRPIDR
- SOLIDR
- PEPEIDR
- HYPEIDR

Pemilihan universe mempertimbangkan ketersediaan data dan evaluasi likuiditas. Ranking likuiditas tersedia di `data/pair_liquidity_ranking.csv`.

Tidak semua pair mempunyai riwayat tiga tahun penuh. Berdasarkan `data/validation_summary.csv`:
- BTCIDR, ETHIDR, SOLIDR, dan XRPIDR memiliki 26.279 candle sejak 9 November 2023.
- PEPEIDR memiliki 24.322 candle sejak 30 Januari 2024.
- HYPEIDR memiliki 9.338 candle sejak 15 Oktober 2025.

Karena itu, penelitian tidak mengklaim seluruh pair memiliki data historis tiga tahun penuh.

## 4. Data dan Validasi

Data historis diperoleh dari endpoint publik Indodax dan disimpan dalam format CSV. Interval data yang digunakan adalah satu jam (1H).

Validasi yang tercatat dalam `data/validation_summary.csv` mencakup:
- Duplikasi candle.
- Missing values.
- Gap data.
- Interval tidak teratur.
- OHLC tidak valid.
- Volume nol.

Pada ringkasan validasi yang tersedia, keenam pair tidak menunjukkan duplikasi, missing values, gap, interval tidak teratur, atau OHLC tidak valid. Terdapat candle dengan volume nol pada setiap pair. Candle tersebut perlu dibedakan dari candle dengan aktivitas perdagangan.

Periode data setiap pair tidak sama. Perbedaan ini menjadi keterbatasan dalam perbandingan lintas aset.

## 5. Strategi Trading

Indikator yang digunakan:
- EMA 20.
- EMA 50.
- RSI 14.

Aturan sinyal yang didokumentasikan:
- Sinyal beli ketika EMA 20 lebih besar daripada EMA 50 dan RSI berada dalam rentang 50–70.
- Kondisi keluar ketika EMA 20 tidak lagi lebih besar daripada EMA 50 atau RSI turun di bawah 45.

Implementasi aktual dan konsistensi fungsi sinyal antara backtest dan forward engine harus merujuk pada kode sumber di folder `src/`.

## 6. Parameter dan Biaya Backtest

Parameter yang tercatat dalam konfigurasi penelitian:

| Parameter | Nilai |
|---|---:|
| Modal awal | Rp100.000.000 |
| Maksimal posisi | 3 |
| Alokasi maksimal per posisi | 30% |
| Full spread asumsi | 0,04% |
| Slippage asumsi per sisi | 0,05% |
| Interval candle | 1 jam |
| Fee OOS utama | 0,2% per sisi |

Spread dan slippage merupakan asumsi simulasi, bukan jaminan biaya eksekusi aktual. Hasil backtest dapat berubah apabila kondisi likuiditas dan biaya pasar berbeda.

## 7. Evaluasi Out-of-Sample

Pengujian OOS fee 0,2% menggunakan batas pemisahan 15 Desember 2025:
- TRAIN: data sampai batas pemisahan.
- TEST: data setelah batas pemisahan.

Hasil berasal dari `data/oos_results_fee02/oos_summary.csv`.

| Metrik | TRAIN | TEST |
|---|---:|---:|
| Modal awal | Rp100,00 juta | Rp100,00 juta |
| Equity akhir | Rp150,09 juta | Rp47,51 juta |
| Return | +50,09% | -52,49% |
| Maximum drawdown | -39,10% | -57,49% |
| Profit factor | 1,094 | 0,732 |
| Completed trades | 1.242 | 560 |

Hasil TEST menunjukkan penurunan equity yang besar. Profit factor di bawah 1 menunjukkan kerugian kotor lebih besar daripada keuntungan kotor berdasarkan perhitungan eksperimen.

Dengan demikian, hasil pengujian belum mendukung kesimpulan bahwa strategi memiliki performa out-of-sample yang menguntungkan dan konsisten.

## 8. Analisis Sensitivitas Fee

Hasil terpisah tersedia pada:
- `data/fee_sensitivity/fee_sensitivity_summary.csv`
- `data/fee_sensitivity/metrics_fee_0.1pct.csv`
- `data/fee_sensitivity/metrics_fee_0.2pct.csv`
- `data/fee_sensitivity/metrics_fee_0.3pct.csv`

| Fee per sisi | Equity akhir | Return | Max drawdown | Transaksi | Profit factor |
|---:|---:|---:|---:|---:|---:|
| 0,1% | Rp198,88 juta | +98,88% | -32,53% | 1.826 | 1,146 |
| 0,2% | Rp89,23 juta | -10,77% | -63,64% | 1.826 | 0,986 |
| 0,3% | Rp22,51 juta | -77,49% | -89,07% | 1.655 | 0,893 |

**Catatan metodologi:** Hasil sensitivitas fee 0,2% berbeda dari hasil OOS TEST fee 0,2%. Keduanya berasal dari eksperimen yang berbeda dan tidak boleh diperlakukan sebagai hasil dari periode yang sama. Perbandingan yang adil memerlukan pemeriksaan periode data, input, dan konfigurasi masing-masing eksperimen.

## 9. Benchmark Bitcoin

File metrik backtest utama mencatat benchmark BTC buy-and-hold sebesar -8,32% pada eksperimen yang bersangkutan.

Angka benchmark tersebut tidak boleh langsung digabungkan dengan hasil fee sensitivity yang mencatat benchmark BTC +130,98%, karena periode atau cakupan eksperimennya berbeda.

Perbandingan strategi dengan benchmark harus menggunakan periode, data awal, dan akhir pengujian yang sama.

## 10. Forward Test

Forward test dijalankan dalam mode DRY_RUN sejak 11 November 2026.

Status terakhir yang telah diperiksa:
- Mode: DRY_RUN.
- Kill switch: tidak aktif.
- Completed trades: 1.
- Open positions: 0.
- CSV trade log: 2 baris, terdiri dari satu BUY dan satu SELL.
- Checkpoint pair: 6.

Forward test belum mencapai sepuluh hari. Oleh karena itu, hasilnya bersifat awal dan belum cukup untuk menyimpulkan profitabilitas strategi.

Aktivitas forward test dan orderbook dicatat dalam folder `data/forward_test/` serta `logs/`.

## 11. Manajemen Risiko dan Batasan

Komponen pengamanan yang terdapat dalam proyek meliputi konfigurasi:
- Kill switch.
- Batas kerugian harian.
- Batas posisi dan alokasi modal.
- Validasi orderbook.
- Validasi minimum order.
- Pencatatan transaksi dan checkpoint.
- Mode DRY_RUN.

Keberadaan konfigurasi atau fungsi tersebut tidak dengan sendirinya membuktikan seluruh kondisi risiko telah teruji. Status implementasi dan hasil pengujiannya perlu merujuk pada audit teknis.

Keterbatasan penelitian:
- Riwayat data setiap pair tidak sama panjang.
- Spread dan slippage menggunakan asumsi simulasi.
- Hasil fee sensitivity dan OOS belum dapat dibandingkan langsung.
- Hasil TEST OOS menunjukkan kerugian.
- Forward test masih berdurasi pendek.
- Sistem belum terbukti aman atau menguntungkan untuk penggunaan dana sungguhan.

## 12. Struktur Proyek

```text
UAS-TRADING-BOT/
├── data/
│   ├── historical_3y/
│   ├── forward_test/
│   ├── backtest/
│   ├── oos_results/
│   ├── oos_results_fee02/
│   └── fee_sensitivity/
├── logs/
├── src/
├── dashboard.html
├── README.md
├── .env.example
└── .gitignore
```

## 13. Dashboard

Dashboard lokal digunakan untuk membantu pemantauan status forward test, saldo, posisi, transaksi, indikator, sinyal, orderbook, dan hasil eksperimen yang tersedia.

Dashboard merupakan sarana pemantauan penelitian dan bukan bukti bahwa strategi telah siap digunakan pada pasar live.

## 14. Kesimpulan

Pada eksperimen OOS dengan fee 0,2% per sisi, strategi menghasilkan return TEST sebesar -52,49%, dengan maximum drawdown -57,49% dan profit factor 0,732.

Hasil ini menunjukkan bahwa strategi belum memiliki performa yang memadai pada periode pengujian di luar sampel. Sensitivitas terhadap biaya transaksi juga menunjukkan bahwa peningkatan fee dapat menurunkan performa secara signifikan.

Forward test telah dimulai pada 11 November 2026, tetapi durasinya belum cukup untuk menjadi bukti profitabilitas jangka panjang.

Kesimpulan penelitian adalah bahwa prototipe trading bot berhasil dikembangkan untuk kebutuhan eksperimen dan evaluasi, tetapi strategi masih memerlukan perbaikan serta pengujian lanjutan. Sistem tidak dinyatakan siap untuk live trading.

## 15. Status Proyek

- [x] Pengumpulan data historis.
- [x] Validasi data historis.
- [x] Perhitungan indikator.
- [x] Backtesting multi-pair.
- [x] Evaluasi OOS.
- [x] Sensitivitas biaya transaksi.
- [x] Benchmark tercatat dalam hasil eksperimen.
- [x] Forward test DRY_RUN dimulai.
- [ ] Audit final konsistensi eksperimen.
- [ ] Finalisasi laporan dan dokumentasi.
- [ ] Pemeriksaan akhir seluruh deliverable.
