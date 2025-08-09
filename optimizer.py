# filepath: optimizer.py
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_aer.primitives import Sampler as AerSampler
from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver


def optimize_portfolio_qaoa(preds):
    """
    Mengoptimalkan portofolio menggunakan QAOA untuk memaksimalkan skor prediksi.
    Memilih antara 1 hingga 2 aset.
    """
    # Buat program kuadratik
    qp = QuadraticProgram()
    for i, asset in enumerate(preds.index):
        qp.binary_var(name=asset)

    # Fungsi Objektif: Maksimalkan total skor prediksi dari aset yang dipilih.
    # Kita hanya mempertimbangkan aset dengan skor positif untuk dibeli (strategi long-only).
    linear_objective = {asset: float(preds[asset]) for asset in preds.index if preds[asset] > 0}
    qp.maximize(linear=linear_objective)

    # Batasan (Constraint): Pilih setidaknya 1 aset, dan maksimal 2 aset.
    # Ini untuk memastikan kita selalu berinvestasi dan tetap terdiversifikasi.
    all_assets = [asset for asset in preds.index]
    qp.linear_constraint(linear={asset: 1 for asset in all_assets}, sense=">=", rhs=1, name="min_one_asset")
    qp.linear_constraint(linear={asset: 1 for asset in all_assets}, sense="<=", rhs=2, name="max_two_assets")
    
    # Siapkan solver QAOA
    # Kita menggunakan AerSampler untuk simulasi di komputer klasik.
    sampler = AerSampler()
    optimizer = COBYLA(maxiter=100)
    qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=1)
    
    # Buat optimizer utama dan selesaikan masalah
    meo = MinimumEigenOptimizer(qaoa)
    result = meo.solve(qp)

    # Ekstrak hasil: aset mana yang dipilih (nilai variabel > 0.5)
    # Cara lama yang menyebabkan error:
    # chosen_assets = [var.name for var in result.variables if var.value > 0.5]
    
    # Cara yang benar untuk mengekstrak hasil di versi Qiskit ini:
    chosen_assets = []
    # result.x adalah array numerik [1., 0., 1., ...]
    # qp.variables adalah daftar objek variabel dalam urutan yang benar
    for i, var in enumerate(qp.variables):
        if result.x[i] > 0.5:
            chosen_assets.append(var.name)
    
    return chosen_assets, result

def optimize_portfolio_classical(preds):
    """
    Mengoptimalkan portofolio menggunakan solver klasik (NumPyMinimumEigensolver) 
    sebagai pembanding yang akurat.
    """
    # Build quadratic program (sama persis dengan versi QAOA)
    qp = QuadraticProgram()
    for asset in preds.index:
        qp.binary_var(name=asset)

    linear_objective = {asset: float(preds[asset]) for asset in preds.index if preds[asset] > 0}
    qp.maximize(linear=linear_objective)

    all_assets = [asset for asset in preds.index]
    qp.linear_constraint(linear={asset: 1 for asset in all_assets}, sense=">=", rhs=1, name="min_one_asset")
    qp.linear_constraint(linear={asset: 1 for asset in all_assets}, sense="<=", rhs=2, name="max_two_assets")

    # Gunakan solver klasik yang dirancang untuk masalah ini
    # NumPyMinimumEigensolver akan menemukan solusi optimal secara eksak.
    classical_solver = NumPyMinimumEigensolver()
    
    # Gunakan MinimumEigenOptimizer seperti pada QAOA, tapi dengan solver klasik
    meo = MinimumEigenOptimizer(classical_solver)
    result = meo.solve(qp)

    # Ekstrak hasil (cara ini sekarang akan berfungsi karena kita menggunakan MinimumEigenOptimizer)
    # Cara lama yang salah:
    # chosen_assets = [var.name for var in result.variables if var.value > 0.5]
    
    # Cara yang benar, sama seperti di fungsi QAOA:
    chosen_assets = []
    for i, var in enumerate(qp.variables):
        if result.x[i] > 0.5:
            chosen_assets.append(var.name)
    
    return chosen_assets, result