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

## Roadmap Optimal (Ringkasan Praktis)

Roadmap ini merangkum tahapan dari laboratorium riset menuju pra-produksi hingga siap enterprise. Detail lengkap tersimpan di img/Roadmap_Optimal.txt. Di README ini disajikan ringkasan operasional yang actionable.

- Phase A — Foundation (Safe MVP)
  - Tujuan: pipeline end-to-end yang stabil & deterministik (data → predict → optimize → backtest → logs).
  - Deliverables: robust ingestion+schema registry+cache, momentum baseline, deterministic backtest, run_log.jsonl, QAOA simulator + classical fallback, manual execution UI.
  - Gates: reproducible backtest (given seed), no-NaN crashes, ingestion success ≥ target, run_log berisi konteks lengkap.

- Phase B — Robustness & Observability
  - Tujuan: sistem tahan gangguan, ter-instrument penuh, safety gates aktif.
  - Deliverables: OTEL traces, Prometheus metrics + Alertmanager, Grafana dashboards; circuit breakers; shadow mode.
  - Gates: canary+metric gates memicu rollback; shadow run menghasilkan log & PnL compare tanpa order.

- Phase C — Controlled Automation & Governance
  - Deliverables: auto-patch agent (PR-only), CI diperluas (static, unit, deterministic backtest, walk-forward, property tests), OPA policy gates, human-in-loop approvals + signed artifacts.
  - Gates: setiap PR auto-patch menyertakan artifacts & approval; PR yang melonggarkan risiko otomatis gagal.

- Phase D — Quantum Integration & Hybrid Ops
  - Deliverables: QPU scheduler + cost-aware planner; hybrid orchestration (AI filter → top-N → QAOA → fallback); benchmark suite dengan uji signifikansi; shadowed quantum decisions.
  - Gates: QAOA menunjukkan peningkatan signifikan secara statistik pada skenario tertentu; fallback aktif saat latency/noise > threshold.

- Phase E — Productize & Enterprise
  - Deliverables: Enterprise API (multi-tenant, quota), SLA tiers & billing, auditability & compliance pack (immutable logs, model cards), opsional SOC2/ISO docs.
  - Gates: siap melayani sandbox customers dengan signed run reports; internal audit lulus.

Cross-cutting: multi-frequency data, feature set kaya (MA, vol, RSI, MACD, sentiment, orderbook), schema versioning; backtest & evaluasi deterministik + walk-forward + market-impact sim + property tests + uji statistik; safety guards & kill-switch; CI/CD berlapis + OPA; observability (OTEL, Prometheus, dashboards).

Prioritized Next Actions (siap dikerjakan sekarang)
- Tambahkan run_log.jsonl (DONE) dan lengkapi fields: features_version, seed, optimizer_meta.
- Implement deterministic --seed di tools/run_backtest.py dan verifikasi reproducibility.
- Tambah parameter slippage & fee di backtest, simpan artifacts.
- Instrument minimal metrics (prediction_latency_ms, qaoa_latency_ms, estimated_return) dan expose endpoint Prometheus.
- Uji fallback solver path: simulasi kegagalan QAOA → sistem tetap berjalan.
- Setup CI minimal (unit + deterministic backtest) mengunggah artifacts.
- Tambah shadow-mode flag untuk menjalankan strategi tanpa eksekusi order.

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

## Hasil Backtest

Kedua strategi diuji pada periode data yang sama dengan `seed` yang sama untuk perbandingan yang adil.

| Metrik | Strategi Momentum Sederhana | **Strategi Hibrid AI-QAOA** |
| :--- | :--- | :--- |
| **Nilai Akhir ($)** | $14,924.84 | **$15,226.13** |
| **Sharpe Ratio (Tahunan)** | 2.63 | **3.14** |
| **Max Drawdown (%)** | -16.84% | **-11.54%** |

### Analisis Hasil

Strategi Hibrid AI-QAOA menunjukkan kinerja yang unggul di semua metrik utama dibandingkan dengan baseline momentum yang kuat. Kemenangan ini menunjukkan keberhasilan pendekatan hibrid:

1.  **Prediktor AI** (`predict_momentum`) berhasil menyediakan sinyal arah yang efektif.
2.  **Optimizer Kuantum** (`optimize_portfolio_qaoa`) berhasil menggunakan sinyal tersebut untuk membangun portofolio yang tidak hanya mengejar return, tetapi juga secara aktif mengelola risiko (terbukti dari Max Drawdown yang jauh lebih rendah).

Kombinasi ini menghasilkan strategi yang lebih efisien dan lebih tangguh.

## Roadmap & Langkah Selanjutnya

Proyek ini telah berhasil membangun fondasi yang kuat untuk riset trading algoritmik. Langkah selanjutnya akan berfokus pada peningkatan setiap modul secara independen:
-   **Peningkatan Model Prediksi:** Bereksperimen dengan model AI yang lebih canggih (misalnya, Transformer, GNN).
-   **Optimisasi Lanjutan:** Menjelajahi algoritma kuantum lain atau menyempurnakan hyperparameter QAOA.
-   **Manajemen Risiko:** Mengimplementasikan *circuit breaker* dan *position sizing* yang lebih dinamis.
-   **Automasi:** Membangun alur kerja CI/CD untuk pengujian strategi otomatis.