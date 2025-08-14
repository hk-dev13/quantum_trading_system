# Sistem Trading Kuantum & Klasik

Proyek ini mengimplementasikan, menguji, dan membandingkan strategi trading algoritmik menggunakan arsitektur modular di Python. Sistem ini dirancang untuk fleksibilitas, memungkinkan perbandingan berbagai model prediksi dan metode optimisasi (baik klasik maupun kuantum).

## Arsitektur Proyek

Proyek ini telah direfaktor menjadi arsitektur modular yang bersih untuk memisahkan berbagai komponen logis:

-   **/src**: Berisi semua logika inti.
    -   `/ingestion`: Mengambil data harga (dengan sistem cache).
    -   `/models`: Modul untuk model prediksi (sederhana dan canggih).
    -   `/optimizer`: Modul untuk logika pemilihan aset/portofolio (klasik dan kuantum).
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

4.  **Jalankan Backtest**: Buka file `tools/run_backtest.py` dan atur variabel `STRATEGY` di bagian atas ke `'momentum'` atau `'qaoa'`. Kemudian, jalankan skrip:
    ```bash
    python tools/run_backtest.py
    ```

## Hasil Terbaru: Perbandingan Strategi Modular

Berikut adalah hasil dari backtest terbaru yang dijalankan pada 5 aset. Sistem sekarang dapat dengan mudah beralih antara strategi yang berbeda.

| Metrik | Strategi Momentum | Strategi Hibrid AI-QAOA |
| :--- | :--- | :--- |
| **Nilai Akhir** | **`$14,924.84`** | `$13,659.58` |
| **Sharpe Ratio** | **`2.63`** | `2.33` |
| **Max Drawdown** | `-16.84%` | **`-16.52%`** |

*(Catatan: Anda mungkin perlu menghasilkan gambar baru untuk setiap strategi.)*

---

## Log Pengembangan

### Evolusi 1: Perjalanan Refactoring ke Arsitektur Modular

Bagian ini mendokumentasikan proses refactoring signifikan yang dilakukan pada proyek ini, mengubahnya dari serangkaian skrip menjadi arsitektur yang modular dan tangguh.

-   **Tantangan & Solusi**:
    1.  **`ModuleNotFoundError` & Lingkungan Virtual**: Diatasi dengan memanggil interpreter Python yang benar dari direktori `.venv`.
    2.  **`ImportError` & Kode Tidak Sinkron**: Diperbaiki dengan menyelaraskan semua modul (`predictor`, `optimizer`) dengan skrip orkestrasi utama.
    3.  **`KeyError: nan` & Penanganan Data**: Diselesaikan dengan membuat fungsi `choose_assets` lebih defensif untuk menangani baris data `NaN` di awal periode backtest.
    4.  **`429 Too Many Requests` & Rate Limiting API**: Diatasi dengan solusi cerdas berupa **sistem caching lokal** untuk menghindari panggilan API yang berlebihan.

-   **Hasil**: Proses ini menghasilkan arsitektur yang bersih dan tangguh, mampu menangani error, data yang tidak valid, dan batasan eksternal.

### Evolusi 2: Arsitektur Strategi Fleksibel

Setelah refactoring berhasil, tujuan selanjutnya adalah untuk membuktikan kekuatan desain baru dengan mengintegrasikan kembali strategi AI-QAOA yang lebih canggih sebagai modul *plug-and-play*.

-   **Tujuan:** Memodifikasi sistem agar dapat menjalankan dan membandingkan beberapa strategi kompleks hanya dengan mengubah satu baris konfigurasi.

-   **Langkah Implementasi:**
    1.  **Modul Optimizer Kuantum:** Logika optimisasi QAOA dipisahkan ke dalam filenya sendiri: `src/optimizer/quantum_optimizer.py`.
    2.  **Modul Prediktor Tingkat Lanjut:** Model prediksi *machine learning* yang dibutuhkan oleh QAOA juga dipisahkan ke `src/models/advanced_predictor.py`.
    3.  **Orkestrator Cerdas:** Skrip `tools/run_backtest.py` diubah secara signifikan. Sebuah "saklar" `STRATEGY` ditambahkan di bagian atas. Skrip sekarang secara dinamis mengimpor modul dan menjalankan alur kerja yang benar.

-   **Tantangan & Solusi: `KeyError: 'x'` di Qiskit**
    *   **Masalah:** Saat menjalankan strategi QAOA, kami mengalami `KeyError: 'x'` dari dalam pustaka Qiskit saat mendefinisikan *budget constraint*.
    *   **Analisis:** Kode secara keliru mencoba memberikan batasan ke satu variabel bernama `'x'`, padahal Qiskit telah membuat banyak variabel biner (`x_0`, `x_1`, ...).
    *   **Solusi:** Memperbaiki cara batasan didefinisikan. Alih-alih `linear={'x': np.ones(n)}`, kami menggunakan sintaks yang benar dengan memberikan array secara langsung: `linear=np.ones(n)`.

-   **Hasil Akhir:** Integrasi berhasil sepenuhnya. Sistem sekarang dapat dengan mulus beralih antara strategi sederhana dan canggih, membuktikan arsitektur modular yang baru sangat fleksibel, kuat, dan siap untuk eksperimen di masa depan.
