# Sistem Trading Kuantum & Klasik

Proyek ini mengimplementasikan, menguji, dan membandingkan strategi trading algoritmik menggunakan arsitektur modular di Python. Sistem ini dirancang untuk fleksibilitas, memungkinkan perbandingan berbagai model prediksi dan metode optimisasi (baik klasik maupun kuantum).

## Arsitektur Proyek

Proyek ini telah direfaktor menjadi arsitektur modular yang bersih untuk memisahkan berbagai komponen logis:

-   **/src**: Berisi semua logika inti.
    -   `/ingestion`: Mengambil data harga (dengan sistem cache).
    -   `/models`: Model prediksi (misalnya, momentum).
    -   `/optimizer`: Logika pemilihan aset/portofolio.
    -   `/backtest`: Mesin untuk menjalankan backtest dan menghitung metrik.
-   **/configs**: File konfigurasi terpusat untuk parameter.
-   **/data**: Direktori untuk data mentah dan cache.
-   **/tools**: Skrip untuk menjalankan alur kerja, seperti `run_backtest.py`.
-   **/.venv**: Lingkungan virtual Python untuk mengelola dependensi.

## Cara Menjalankan

1.  **Siapkan Lingkungan**: Pastikan Anda memiliki Python dan telah membuat lingkungan virtual.
    ```bash
    python -m venv .venv
    ```

2.  **Aktifkan Lingkungan**:
    -   **Windows (PowerShell)**:
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
    -   **macOS/Linux**:
        ```bash
        source .venv/bin/activate
        ```

3.  **Instal Dependensi**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Jalankan Backtest**: Untuk menjalankan simulasi lengkap, gunakan skrip `run_backtest.py`.
    ```bash
    python tools/run_backtest.py
    ```
    Skrip akan mengambil data (menggunakan cache jika tersedia), menjalankan prediksi, memilih aset, melakukan backtest, dan menampilkan hasil serta grafik kinerja.

## Hasil Terbaru: Strategi Momentum Sederhana (5 Aset)

Berikut adalah hasil dari backtest terbaru yang dijalankan pada 5 aset (`bitcoin`, `ethereum`, `solana`, `cardano`, `dogecoin`) menggunakan strategi momentum sederhana.

-   **Nilai Akhir Portofolio**: `$14,924.84`
-   **Sharpe Ratio Tahunan**: `2.63`
-   **Maximum Drawdown**: `-16.84%`

![Kinerja Strategi Momentum Sederhana](img/strategy_performance_momentum.png)

*(Catatan: Anda mungkin perlu menghasilkan gambar baru dengan nama file yang sesuai untuk mencerminkan hasil ini.)*

---

## Log Pengembangan: Perjalanan Refactoring ke Arsitektur Modular

Bagian ini mendokumentasikan proses refactoring signifikan yang dilakukan pada proyek ini, mengubahnya dari serangkaian skrip menjadi arsitektur yang modular dan tangguh.

### 1. Tujuan Awal: Arsitektur Baru

Tujuan utamanya adalah untuk merefaktor basis kode agar lebih bersih, modular, dan mudah dikelola. Rencananya adalah memisahkan logika ke dalam direktori-direktori spesifik: `src` (untuk logika inti seperti `ingestion`, `models`, `optimizer`), `configs` (untuk konfigurasi), dan `tools` (untuk skrip yang dapat dieksekusi).

### 2. Tantangan & Solusi

Dalam prosesnya, kami menghadapi serangkaian tantangan dunia nyata:

*   **Tantangan 1: `ModuleNotFoundError` & Lingkungan Virtual**
    *   **Masalah:** Skrip gagal berjalan dengan error `ModuleNotFoundError: No module named 'pandas'`, meskipun `requirements.txt` sudah ada.
    *   **Analisis:** Skrip dijalankan menggunakan interpreter Python sistem, bukan interpreter dari lingkungan virtual proyek (`.venv`), di mana semua dependensi terinstal.
    *   **Solusi:** Memperbaiki perintah eksekusi untuk secara eksplisit menggunakan interpreter Python dari `.venv/Scripts/python.exe`. Kami juga harus menggunakan operator `&` di PowerShell untuk menangani path yang berisi spasi (`& .\.venv\Scripts\python.exe tools/run_backtest.py`).

*   **Tantangan 2: `ImportError` & Kode yang Tidak Sinkron**
    *   **Masalah:** Setelah memperbaiki masalah lingkungan, kami mendapatkan `ImportError: cannot import name 'function_name'`. Ini terjadi untuk `predict_momentum` dan `choose_assets`.
    *   **Analisis:** Skrip orkestrasi utama (`run_backtest.py`) telah diperbarui untuk menggunakan fungsi-fungsi baru yang lebih sederhana, tetapi file-file modul (`predictor.py`, `optimizer.py`) masih berisi kode lama yang lebih kompleks dari sebelum refactoring.
    *   **Solusi:** Menimpa isi dari `predictor.py` dan `optimizer.py` dengan versi kode baru yang telah disederhanakan agar selaras dengan arsitektur dan skrip utama.

*   **Tantangan 3: `KeyError: nan` & Penanganan Data**
    *   **Masalah:** Alur kerja gagal saat proses optimisasi dengan `KeyError: nan`.
    *   **Analisis:** Fungsi `predict_momentum` menghasilkan nilai `NaN` (Not a Number) untuk beberapa hari pertama (karena *rolling window*). Fungsi `choose_assets` kemudian mencoba menggunakan `NaN` sebagai kunci untuk mengakses data, yang menyebabkan error.
    *   **Solusi:** Membuat fungsi `choose_assets` menjadi lebih "defensif". Kami menambahkan logika untuk memeriksa apakah satu baris data penuh dengan `NaN` (`.isna().all()`), dan jika ya, melompati hari tersebut tanpa membuat keputusan trading.

*   **Tantangan 4: `429 Too Many Requests` & Rate Limiting API**
    *   **Masalah:** Setelah semua bug kode diperbaiki, eksekusi terhenti oleh error `429 Client Error` dari CoinGecko API.
    *   **Analisis:** Skrip membuat terlalu banyak permintaan API dalam waktu singkat, memicu mekanisme *rate limiting* dari CoinGecko. Menambahkan jeda `time.sleep(1)` sederhana pun tidak cukup.
    *   **Solusi Cerdas:** Mengimplementasikan **sistem caching lokal**. Data yang diambil dari API sekarang disimpan dalam file `data/price_history_cache.csv`. Saat skrip dijalankan lagi, ia akan memuat data dari file cache jika data tersebut masih baru (kurang dari 24 jam), menghindari panggilan API yang tidak perlu sama sekali.

### 3. Hasil Akhir: Sistem yang Tangguh

Setelah mengatasi serangkaian tantangan ini, alur kerja backtest berhasil dijalankan dari awal hingga akhir. Proses ini tidak hanya menghasilkan arsitektur yang lebih bersih, tetapi juga membuktikan ketangguhannya dengan menangani error, data yang tidak valid, dan batasan eksternal secara cerdas.
