# Quantum Trading System

Proyek ini mengimplementasikan dan membandingkan strategi trading menggunakan optimizer klasik dan optimizer kuantum (QAOA) untuk pemilihan aset kripto.

---

## Hasil Terbaru: Backtest dengan Prediktor ML (per 2025-08-09)

Hasil ini didapat setelah meng-upgrade prediktor dari Moving Average sederhana ke model Machine Learning (Logistic Regression) dan menambahkan metrik evaluasi risiko.

### Metrik Kinerja

| Metric             | Classical Optimizer | QAOA Optimizer |
|--------------------|---------------------|----------------|
| **Final Value**    | $15,044.21          | $15,268.51     |
| **Sharpe Ratio**   | 2.75                | 2.83           |
| **Max Drawdown**   | -14.76%             | -14.76%        |

### Grafik Performa

![Perbandingan Performa dengan Prediktor ML](img/Strategy_performance(ML_Predictor).png)

---

## Arsip Hasil Terdahulu

### Hasil Awal (Prediktor Moving Average)

*   **Run 1:**
    *   Optimizer Klasik: $12,938.80
    *   Optimizer QAOA: $13,504.94
### Grafik Performa

![Perbandingan Performa dengan Prediktor ML](img/Strategy_ferformance_ClassicVSVAOA(quantum).png)



*   **Run 2 (menunjukkan variabilitas):**
    *   Optimizer Klasik: $12,938.80
    *   Optimizer QAOA: $11,304.30
### Grafik Performa

![Perbandingan Performa dengan Prediktor ML](img/optimizer_classicVSQAOA(quantum).png)