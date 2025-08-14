# Deskripsi: Konfigurasi utama untuk proyek.

# Aset yang akan dianalisis
ASSETS = ["bitcoin", "ethereum", "solana", "cardano", "dogecoin"]

# Parameter untuk pengambilan data
DAYS_HISTORY = 90

# Parameter untuk strategi
MA_WINDOW = 7

# Parameter untuk backtest
INITIAL_CAPITAL = 10000

# --- TAMBAHKAN PARAMETER SPESIFIK QAOA DI SINI ---

# Jumlah aset teratas (berdasarkan prediksi) yang akan dioptimalkan oleh QAOA.
# Ini adalah bagian 'AI' dari strategi hibrid.
QAOA_TOP_N_ASSETS = 3

# Faktor 'q' dalam fungsi objektif Markowitz.
# Menyeimbangkan antara return (mu) dan risiko (sigma).
# q = 1.0 -> Hanya fokus pada return
# q = 0.0 -> Hanya fokus pada menghindari risiko
# q = 0.5 -> Keseimbangan antara keduanya
OBJECTIVE_Q_FACTOR = 0.5
