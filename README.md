# UAS Trading Bot — Indodax

## 1. Deskripsi Proyek

Proyek ini mengembangkan dan mengevaluasi trading bot berbasis indikator teknikal untuk beberapa pasangan aset kripto IDR di Indodax.

Pengujian dilakukan menggunakan data historis, simulasi biaya transaksi, serta evaluasi out-of-sample (OOS).

## 2. Teknologi

- Python
- Pandas
- NumPy
- Requests
- Indodax Public API
- Git
- HTML, CSS, dan JavaScript untuk dashboard

## 3. Pasangan Aset

- BTCIDR
- ETHIDR
- XRPIDR
- SOLIDR
- PEPEIDR
- HYPEIDR

**Catatan:** Tidak semua pasangan memiliki riwayat data tiga tahun penuh.

## 4. Strategi Trading

Indikator yang digunakan:
- EMA 20
- EMA 50
- RSI 14

Sinyal beli menggunakan kondisi EMA 20 di atas EMA 50 dan RSI dalam rentang 50–70, dengan validasi data perdagangan.

## 5. Asumsi Backtest

- Modal awal: Rp100.000.000
- Biaya transaksi simulasi: 0,1% per sisi
- Full spread asumsi: 0,04%
- Slippage asumsi: 0,05% per sisi
- Maksimal posisi: 3
- Alokasi maksimal: 30%

Asumsi biaya merupakan parameter simulasi dan bukan klaim biaya aktual untuk seluruh transaksi Indodax.

## 6. Hasil Evaluasi Out-of-Sample

| Metrik | TRAIN | TEST |
|---|---:|---:|
| Return | +124,85% | -30,06% |
| CAGR | +47,13% | -32,81% |
| Maximum Drawdown | -22,00% | -40,32% |
| Profit Factor | 1,264 | 0,850 |
| Jumlah Transaksi | 1.242 | 574 |
| Win Rate | 26,25% | 22,30% |

Hasil menunjukkan strategi memperoleh keuntungan pada data TRAIN, tetapi mengalami kerugian pada data TEST. Hal ini menunjukkan strategi belum terbukti memiliki performa yang konsisten pada data yang belum digunakan untuk pelatihan.

## 7. Struktur Proyek

- `src/` — script pengolahan data, indikator, backtest, dan pengambilan order book.
- `data/` — data historis dan hasil pengujian.
- `logs/` — direktori pencatatan forward test.
- `dashboard.html` — dashboard evaluasi lokal.
- `.gitignore` — pengaturan file yang tidak disertakan dalam Git.

## 8. Forward Test

Pengumpulan snapshot order book dilakukan secara berkala menggunakan Windows Task Scheduler.

Periode pengujian aktual dan durasinya harus dicatat berdasarkan data yang benar-benar terkumpul. Pengujian tidak boleh dianggap memenuhi periode sepuluh hari apabila durasi aktualnya belum mencapai sepuluh hari.

## 9. Batasan

- Hasil backtest merupakan simulasi, bukan jaminan keuntungan.
- PEPEIDR dan HYPEIDR belum memiliki riwayat data tiga tahun penuh.
- Hasil TEST menunjukkan strategi belum robust.
- Forward test perlu dievaluasi berdasarkan catatan aktual.
- Sistem belum boleh dianggap sebagai bot live trading yang siap menggunakan dana sungguhan.

## 10. Status Proyek

Dokumentasi dan dashboard evaluasi sedang disiapkan. Pengujian lanjutan, pencatatan forward test, dan evaluasi sistem masih diperlukan.