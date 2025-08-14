# Sistem Trading Kuantum & Klasik

Proyek ini mengimplementasikan, menguji, dan membandingkan strategi trading algoritmik menggunakan arsitektur modular di Python. Sistem ini dirancang untuk fleksibilitas, memungkinkan perbandingan berbagai model prediksi dan metode optimisasi.

## Arsitektur Proyek

Proyek ini telah direfaktor menjadi arsitektur modular yang bersih untuk memisahkan berbagai komponen logis:

-   **/src**: Berisi semua logika inti.
    -   `/ingestion`: Mengambil data harga (dengan sistem cache).
    -   `/models`: Modul untuk model prediksi (sederhana dan canggih).
    -   `/optimizer`: Modul untuk logika pemilihan aset/portofolio.
    -   `/backtest`: Mesin untuk menjalankan backtest.
-   **/configs**: File konfigurasi terpusat.
-   **/data**: Direktori untuk data mentah dan cache.
-   **/tools**: Skrip untuk menjalankan alur kerja.
-   **/.venv**: Lingkungan virtual Python.

## Cara Menjalankan

1.  **Siapkan & Aktifkan Lingkungan**:
    ```powershell
    # Windows
    .\.venv\Scripts\Activate.ps1
    ```
    ```bash
    # macOS/Linux
    source .venv/bin/activate
    ```
2.  **Instal Dependensi**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Jalankan Backtest**: Buka `tools/run_backtest.py` dan atur `STRATEGY` ke `'momentum'` atau `'qaoa'`.
    ```bash
    python tools/run_backtest.py
    ```

## Hasil Terbaru: Perbandingan Strategi & Model

| Metrik | Strategi Momentum | QAOA + Regresi Logistik | QAOA + LSTM |
| :--- | :--- | :--- | :--- |
| **Nilai Akhir** | **`$14,924.84`** | `$13,659.58` | `$9,655.43`|
| **Sharpe Ratio** | **`2.63`** | `2.33` | `-0.22`|
| **Max Drawdown** | `-16.84%` | **`-16.52%`**| `-19.46%`|

---

## Log Pengembangan

### Evolusi 1: Refactoring ke Arsitektur Modular
-   **Tantangan**: `ModuleNotFoundError`, `ImportError`, `KeyError: nan`, `429 Too Many Requests`.
-   **Solusi**: Memperbaiki path lingkungan virtual, menyelaraskan modul, menambahkan penanganan NaN, dan mengimplementasikan sistem caching.
-   **Hasil**: Arsitektur yang bersih, tangguh, dan efisien.

### Evolusi 2: Arsitektur Strategi Fleksibel
-   **Tujuan**: Mengintegrasikan kembali strategi AI-QAOA sebagai modul *plug-and-play*.
-   **Tantangan**: `KeyError: 'x'` di Qiskit saat mendefinisikan *budget constraint*.
-   **Solusi**: Memperbaiki sintaks definisi batasan untuk Qiskit.
-   **Hasil**: Sistem yang dapat dengan mulus beralih antara strategi sederhana dan canggih.

### Evolusi 3: Peningkatan Model AI (LSTM)
-   **Tujuan**: Meningkatkan "kecerdasan" prediktor untuk memberikan sinyal yang lebih baik ke optimizer kuantum.
-   **Langkah**:
    1.  Menambahkan `tensorflow` ke `requirements.txt`.
    2.  Membuat `lstm_predictor.py` untuk merangkum logika *deep learning*.
    3.  Mengganti prediktor regresi logistik dengan prediktor LSTM dalam alur kerja QAOA.
-   **Tantangan**: Performa eksekusi yang sangat lambat.
-   **Analisis**: Model LSTM dibuat dan dikompilasi di **setiap hari** dalam *loop* backtest, yang sangat tidak efisien.
-   **Solusi**: Merefaktor kode untuk **membuat model hanya satu kali** di luar *loop*, dan hanya melatih ulang bobotnya di dalam *loop*. Ini adalah praktik standar dan secara dramatis meningkatkan kecepatan eksekusi.
-   **Hasil Akhir**: Model LSTM pertama menghasilkan kinerja yang lebih rendah, yang merupakan hasil riset yang berharga. Ini menunjukkan bahwa model yang lebih kompleks tidak selalu lebih baik dan menyoroti pentingnya *hyperparameter tuning*. Eksperimen ini dimungkinkan oleh arsitektur modular yang fleksibel.
