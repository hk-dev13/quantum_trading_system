# Rencana Proyek Terpadu: Quantum AI Trading System

Dokumen ini menggabungkan visi strategis jangka panjang dengan rencana eksekusi taktis untuk membangun platform trading Quantum AI yang canggih, aman, dan siap untuk skala enterprise.

---

## BAGIAN 1: VISI STRATEGIS & PETA JALAN JANGKA PANJANG

Bagian ini menguraikan visi, arsitektur, fase pengembangan, dan tujuan komersial proyek.

### 1. Visi & Tujuan Utama
- **Visi**: Membangun platform trading berbasis Quantum AI yang mampu melakukan optimasi portofolio dan prediksi pasar real-time dengan kecepatan dan akurasi di atas sistem konvensional.
- **Target Pengguna Awal**: Trader profesional, hedge fund kecil–menengah, dan tim riset keuangan.
- **Nilai Jual Unik**:
    - Memadukan AI klasik (Machine Learning) dengan Quantum Optimization (QAOA / VQE).
    - Sistem modular yang bisa digunakan perusahaan lain lewat API.
    - Infrastruktur yang dapat diskalakan untuk sektor selain crypto (misalnya energi, logistik, supply chain).

### 2. Arsitektur Sistem
- **Data Layer**: Binance API, CoinGecko API, Kafka/WebSocket untuk streaming.
- **AI Prediction Layer**: Model ML (LSTM, XGBoost) untuk tren dan NLP untuk sentimen.
- **Quantum Optimization Layer**: QAOA/VQE dari Qiskit untuk komposisi portofolio optimal.
- **Web & API Layer**: Frontend (Next.js/React), Backend (Node.js + FastAPI), API publik/private.
- **Security & Compliance Layer**: Enkripsi data, audit log, dukungan KYC/AML.

### 3. Fase Implementasi
- **Fase Awal (MVP Internal)**: Fokus pada data collector, model ML dasar (BTC/ETH), QAOA sederhana, dan dashboard internal.
- **Fase Kedua (Beta Private)**: Menambah integrasi multi-exchange, analisis sentimen, dan API private untuk klien beta.
- **Fase Ketiga (Produk Komersial)**: API publik, integrasi sektor non-crypto, dan infrastruktur cloud-scale.

### 4. Mitigasi Risiko & Prinsip Inti
- **Hybrid-first**: Quantum untuk riset, produksi berjalan dengan fallback klasik yang andal.
- **Fail-safe > Auto-everything**: Otomatisasi harus aman. Patch otomatis hanya melalui PR & human approval.
- **Observability-by-default**: Setiap event harus dapat dilacak (OpenTelemetry).
- **Governance & Audit**: Semua perubahan terikat pada kebijakan dan memiliki jejak audit.
- **Shadowing & Canary**: Semua perubahan diuji secara paralel di production feed sebelum rilis penuh.

---

## BAGIAN 2: EXECUTION STARTER KIT (LANGKAH SEGERA)

Bagian ini merinci langkah-langkah konkret, struktur, dan tools yang dibutuhkan untuk memulai implementasi (Sprint 0-1).

### A. Struktur Direktori Proyek
```
/data/                # Data mentah & terkurasi (dengan versi + skema)
/src/
  /ingestion/         # Adapter untuk CoinGecko, API exchange (+ tes)
  /features/          # Logika untuk MA, momentum, volume, sentimen
  /models/            # Model dari MA_v1 hingga LSTM/XGBoost
  /optimizer/
    /qaoa_sim/        # Riset & simulasi QAOA
    /classical/       # Fallback solver (QP/SA)
  /execution/         # Skrip untuk eksekusi manual (bukan order live)
  /backtest/          # Harness untuk backtesting & simulasi market impact
  /monitoring/        # Konfigurasi OpenTelemetry, metrik, dan alert
/policies/            # Kebijakan OPA (risiko, rollout)
/configs/             # Konfigurasi: assets.yml, alpha_beta.yml, slas.yml
/tools/               # Skrip bantuan: run_backtest.py, snapshotter.py
```

### B. Konfigurasi Inti
- `configs/assets.yml`: Daftar aset target dan sumber datanya.
- `configs/alpha_beta.yml`: Koefisien untuk fungsi objektif (α untuk return, β untuk risiko).
- `configs/slas.yml`: Target SLOs (latensi, PnL drift, error rate).
- `configs/rollout.yml`: Langkah-langkah canary deployment dan gerbang metrik.

### C. Logging & Audit Trail
- **`run_log.jsonl`**: Setiap eksekusi mencatat log dalam format JSONL terstruktur dengan tanda tangan digital.
- **`portfolio_snapshot.png`**: Gambar snapshot portofolio dihasilkan secara otomatis setiap kali dijalankan.

### D. Guardrails & Self-Healing
- **Circuit Breaker**: Di dalam optimizer, jika latensi QAOA melebihi ambang batas, sistem secara otomatis beralih ke fallback solver klasik.
- **Shadow Mode**: Strategi atau patch baru selalu berjalan dalam mode shadow (tanpa order live) untuk perbandingan.
- **Kill Switch**: Mekanisme darurat berlapis (soft: kurangi ukuran posisi, hard: hentikan entri baru, darurat: likuidasi posisi).

### E. Governance & Proses Perubahan
- **Auto-Patch via PR**: Agen otomatisasi hanya dapat mengusulkan perubahan dengan membuat Pull Request (PR), tidak pernah push langsung ke `main`.
- **Human-in-the-loop**: Setiap PR yang memengaruhi risiko atau eksekusi memerlukan persetujuan manual dari manusia setelah melewati gerbang CI/CD.

### F. Checklist Tugas Prioritas (Sprint Awal)
1.  **Bangun Ingestion**: Implementasikan pengumpul data dengan schema registry dan cache last-good.
2.  **Implementasikan Model Dasar**: Buat model prediksi sederhana (misalnya, Moving Average) dan translasikan skornya ke koefisien objektif (α/β).
3.  **Siapkan Optimizer**: Tambahkan fallback solver klasik dan simulator QAOA untuk riset.
4.  **Buat Backtest Harness**: Harus deterministik (dapat direproduksi dengan seed) dan mensimulasikan market impact & fee.
5.  **Kembangkan Logging**: Buat writer untuk `run_log.jsonl` dan `snapshotter.png`.
6.  **Aktifkan Shadow Mode**: Implementasikan pipeline untuk shadow trading.
7.  **Definisikan Kill Switch**: Tentukan logika dan alur untuk mekanisme kill switch.
8.  **Bangun CI/CD Awal**: Konfigurasikan pipeline yang menjalankan unit test, analisis keamanan statis (Semgrep/Bandit), dan backtest deterministik.

