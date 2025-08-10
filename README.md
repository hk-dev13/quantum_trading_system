# Quantum Trading System

Proyek ini mengimplementasikan dan membandingkan strategi trading menggunakan optimizer klasik dan kuantum (QAOA) untuk pemilihan aset kripto.

---

## Hasil Terbaru: Strategi Hibrid dengan Model Risiko Markowitz (5 Aset)

Ini adalah hasil dari konfigurasi sistem yang paling canggih, diuji pada 5 aset (`bitcoin`, `ethereum`, `solana`, `cardano`, `dogecoin`).

*   **Strategi Klasik:** Menggunakan optimizer eksak pada **semua 5 aset**.
*   **Strategi Hibrid QAOA:** Menggunakan AI untuk memilih **3 aset teratas**, kemudian dioptimalkan dengan QAOA.
*   **Model Objektif:** Kedua strategi menggunakan fungsi objektif modern (Markowitz) yang menyeimbangkan prediksi return (dari AI) dengan risiko (dari matriks kovarians historis).

### Metrik Kinerja (per 2025-08-10)

| Metric             | Classical Optimizer | Hybrid QAOA Optimizer |
|--------------------|---------------------|-----------------------|
| **Final Value**    | $13,069.11          | $13,353.55            |
| **Sharpe Ratio**   | 1.82                | 1.96                  |
| **Max Drawdown**   | -18.03%             | -18.03%               |

### Grafik Performa

![Perbandingan Performa dengan Model Risiko Markowitz](img/strategy_performance_markowitz.png)
![Perbandingan Drawdown dengan Model Risiko Markowitz](img/strategy_drawdown_markowitz.png)

### Analisis
Implementasi model risiko berbasis kovarians merupakan **peningkatan signifikan**. Hal ini memungkinkan kedua strategi untuk secara aktif berdagang di lingkungan yang lebih kompleks (5 aset). Strategi Hibrid AI-Kuantum menunjukkan keunggulan tipis dalam hal return akhir dan return yang disesuaikan dengan risiko (Sharpe Ratio).

---

## Timeline Proyek & Evolusi Strategi

Berikut adalah rekam jejak evolusi proyek ini dari konsep awal hingga kondisi saat ini.

### Fase 1: Konsep Awal & Implementasi Dasar
*   **Tujuan:** Membangun kerangka kerja dasar untuk membandingkan optimizer klasik dan kuantum.
*   **Prediktor:** Sinyal sederhana berbasis *Moving Average Crossover*.
*   **Optimizer:** QAOA vs Klasik, dengan fungsi objektif yang hanya memaksimalkan prediksi return.
*   **Aset:** 3 Aset (`bitcoin`, `ethereum`, `solana`).
*   **Temuan:** QAOA menunjukkan potensi awal tetapi hasilnya tidak stabil, menyoroti pentingnya kualitas sinyal input.

### Fase 2: Peningkatan Prediktor & Analisis Risiko
*   **Tujuan:** Meningkatkan kualitas sinyal dan menambahkan metrik risiko.
*   **Tindakan:**
    1.  Mengganti prediktor *Moving Average* dengan model *Machine Learning* (Logistic Regression).
    2.  Menambahkan visualisasi *Drawdown* untuk menganalisis risiko.
*   **Temuan:** Kinerja sistem meningkat secara dramatis. Strategi QAOA secara konsisten mengungguli strategi klasik dengan selisih tipis, menghasilkan **Sharpe Ratio 2.83**. Ini menjadi *baseline* emas untuk perbandingan selanjutnya.

### Fase 3: Uji Stres & Skalabilitas
*   **Tujuan:** Menguji bagaimana sistem menangani kompleksitas yang lebih tinggi.
*   **Tindakan:** Menambah jumlah aset dari 3 menjadi 5.
*   **Temuan:** Kinerja QAOA **menurun drastis**, sementara optimizer klasik tetap tangguh. Ini membuktikan bahwa sirkuit QAOA yang sederhana (`reps=1`) kesulitan menemukan solusi yang baik di ruang pencarian yang lebih besar.

### Fase 4: Strategi Hibrid AI-Kuantum
*   **Tujuan:** Mengatasi masalah skalabilitas QAOA.
*   **Tindakan:** Mengimplementasikan pendekatan hibrid: AI digunakan untuk **memfilter 3 kandidat aset teratas**, kemudian QAOA dijalankan pada subset yang lebih kecil ini.
*   **Temuan:** Pendekatan ini berhasil **meningkatkan kembali kinerja QAOA**, membuktikan validitas strategi hibrid untuk mengelola kompleksitas.

### Fase 5: Model Risiko Canggih (Markowitz)
*   **Tujuan:** Membuat keputusan investasi yang lebih cerdas dengan menyeimbangkan return dan risiko secara formal.
*   **Tindakan:** Mengganti fungsi objektif sederhana dengan **model portofolio Markowitz**, yang memasukkan matriks kovarians historis sebagai representasi risiko.
*   **Temuan:** Ini adalah **peningkatan paling signifikan pada logika inti sistem**. Kedua strategi menjadi jauh lebih baik dalam menavigasi pasar dengan 5 aset. Strategi Hibrid AI-Kuantum kembali menunjukkan keunggulan tipis, mencapai hasil yang terdokumentasi di bagian atas README ini.