# LAPORAN AKHIR
# Pengembangan dan Evaluasi Trading Bot Multi-Pair pada Exchange Indodax

## 1. Pendahuluan

Penelitian ini bertujuan mengembangkan prototipe trading bot berbasis indikator teknikal untuk beberapa pasangan aset kripto terhadap Rupiah (IDR) pada exchange Indodax. Sistem dirancang untuk mengolah data historis, menghasilkan sinyal perdagangan, melakukan simulasi backtesting, dan menjalankan forward test dalam mode DRY_RUN.

Evaluasi dilakukan untuk mengetahui konsistensi strategi, pengaruh biaya transaksi, serta keterbatasan sistem sebelum kemungkinan pengembangan lebih lanjut.

## 2. Metodologi

### 2.1 Pengumpulan Data

Data historis diperoleh dari endpoint publik Indodax dengan interval candle satu jam. Universe penelitian terdiri dari BTCIDR, ETHIDR, XRPIDR, SOLIDR, PEPEIDR, dan HYPEIDR.

Panjang riwayat data berbeda untuk setiap pair. Empat pair memiliki data sejak November 2023, PEPEIDR sejak Januari 2024, dan HYPEIDR sejak Oktober 2025.

### 2.2 Validasi Data

Validasi mencakup pemeriksaan duplikasi timestamp, missing values, gap data, interval candle, nilai OHLC, dan volume perdagangan.

Ringkasan validasi yang tersedia menunjukkan tidak terdapat duplikasi, missing values, gap, interval tidak teratur, maupun OHLC tidak valid pada keenam pair. Candle dengan volume nol tetap ditemukan dan diperlakukan sebagai keterbatasan aktivitas pasar.

### 2.3 Strategi

Strategi menggunakan:
- Exponential Moving Average periode 20.
- Exponential Moving Average periode 50.
- Relative Strength Index periode 14.

Sinyal beli didasarkan pada EMA 20 yang lebih besar daripada EMA 50 dan RSI dalam rentang 50–70. Kondisi keluar didasarkan pada perubahan hubungan EMA atau RSI di bawah 45.

### 2.4 Backtesting dan OOS

Modal awal simulasi sebesar Rp100.000.000. Pengujian OOS fee 0,2% per sisi menggunakan batas pemisahan 15 Desember 2025. Data sampai batas tersebut digunakan sebagai TRAIN, sedangkan data setelahnya digunakan sebagai TEST.

### 2.5 Forward Test

Forward test dijalankan menggunakan mode DRY_RUN sejak 11 November 2026. Sistem memproses data pasar, indikator, sinyal, dan simulasi transaksi tanpa mengirim order sungguhan ke exchange.

## 3. Hasil Penelitian

### 3.1 Hasil OOS Fee 0,2%

| Metrik | TRAIN | TEST |
|---|---:|---:|
| Modal awal | Rp100,00 juta | Rp100,00 juta |
| Equity akhir | Rp150,09 juta | Rp47,51 juta |
| Return | +50,09% | -52,49% |
| Maximum drawdown | -39,10% | -57,49% |
| Profit factor | 1,094 | 0,732 |
| Completed trades | 1.242 | 560 |

Hasil TRAIN menunjukkan return positif, tetapi hasil TEST menunjukkan penurunan equity yang besar. Profit factor TEST di bawah 1 menunjukkan strategi belum menghasilkan keuntungan yang konsisten pada periode out-of-sample.

### 3.2 Sensitivitas Biaya Transaksi

Eksperimen sensitivitas fee pada keseluruhan data menghasilkan:

| Fee per sisi | Equity akhir | Return | Maximum drawdown |
|---:|---:|---:|---:|
| 0,1% | Rp198,88 juta | +98,88% | -32,53% |
| 0,2% | Rp89,23 juta | -10,77% | -63,64% |
| 0,3% | Rp22,51 juta | -77,49% | -89,07% |

Hasil menunjukkan bahwa biaya transaksi mempunyai pengaruh besar terhadap performa simulasi. Eksperimen sensitivitas ini berbeda dari pengujian OOS sehingga hasilnya tidak dibandingkan sebagai satu periode pengujian yang sama.

### 3.3 Forward Test

Forward test telah dimulai pada 11 November 2026 dalam mode DRY_RUN. Pada pemeriksaan terakhir, sistem mencatat satu transaksi selesai, tidak memiliki posisi terbuka, dan kill switch tidak aktif.

Pengujian belum berlangsung selama sepuluh hari. Oleh karena itu, hasil forward test masih bersifat awal dan belum dapat digunakan untuk menyimpulkan profitabilitas jangka panjang.

## 4. Pembahasan

Hasil pengujian menunjukkan perbedaan antara performa TRAIN dan TEST. Strategi yang menghasilkan return positif pada TRAIN mengalami kerugian pada TEST. Hal ini mengindikasikan bahwa strategi belum cukup robust terhadap perubahan kondisi pasar.

Sensitivitas fee juga memperlihatkan bahwa biaya transaksi dapat mengubah hasil simulasi secara material. Oleh karena itu, asumsi fee, spread, slippage, dan likuiditas perlu diperhatikan dalam evaluasi strategi.

Perbedaan panjang data historis antar-pair juga menjadi keterbatasan penelitian. Hasil forward test yang masih singkat belum cukup untuk mengonfirmasi performa strategi pada kondisi pasar berjalan.

## 5. Kesimpulan

Prototipe trading bot multi-pair berhasil dikembangkan untuk pengumpulan data, perhitungan indikator, backtesting, evaluasi OOS, simulasi biaya transaksi, dan forward test DRY_RUN.

Namun, hasil OOS TEST fee 0,2% menunjukkan return -52,49% dengan maximum drawdown -57,49% dan profit factor 0,732. Dengan hasil tersebut, strategi belum dapat dinyatakan menguntungkan atau robust.

Sistem masih berada pada tahap penelitian dan simulasi. Sistem tidak direkomendasikan untuk penggunaan dana sungguhan berdasarkan hasil pengujian saat ini.

## 6. Keterbatasan dan Pengembangan Lanjutan

Pengembangan berikutnya dapat mencakup:
1. Evaluasi ulang aturan entry dan exit.
2. Pengujian ketahanan strategi pada beberapa kondisi pasar.
3. Pengujian biaya transaksi berdasarkan kondisi order book aktual.
4. Penambahan durasi forward test.
5. Evaluasi konsistensi sinyal antara backtest dan forward engine.
6. Pengujian tambahan terhadap mekanisme manajemen risiko.

## 7. Pernyataan Pengujian

Seluruh hasil yang dilaporkan merupakan hasil eksperimen dan simulasi berdasarkan data serta konfigurasi yang tersedia. Forward test berjalan dalam mode DRY_RUN dan bukan transaksi live. Tidak ada klaim bahwa strategi telah menghasilkan keuntungan aktual atau siap digunakan untuk perdagangan dengan dana sungguhan.
