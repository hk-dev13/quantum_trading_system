# Deskripsi: Algoritma untuk optimasi portofolio menggunakan metode klasik dan kuantum.
#
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_aer.primitives import Sampler as AerSampler
from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver

def optimize_portfolio_qaoa(predictions):
    """Optimasi portofolio menggunakan QAOA."""
    assets = predictions.index.tolist()
    mu = predictions.values
    n_assets = len(assets)

    # Buat Quadratic Program
    qp = QuadraticProgram("PortfolioOptimization")
    qp.binary_var_list(n_assets, name="x")
    
    # Fungsi objektif: maksimalkan return yang diprediksi
    # Kita hanya menggunakan bagian linear karena ini adalah pemilihan aset, bukan alokasi
    qp.maximize(linear=mu)
    
    # Setup QAOA
    sampler = AerSampler()
    optimizer = COBYLA()
    # Kembalikan ke reps=1 yang terbukti lebih baik
    qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=1) # <-- UBAH KEMBALI KE 1

    # Buat optimizer dan selesaikan masalah
    optimizer_qaoa = MinimumEigenOptimizer(qaoa)
    result = optimizer_qaoa.solve(qp)
    
    # Terjemahkan hasil
    # FIX: Nilai dalam result.x bisa berupa float yang sangat dekat dengan 1.0 (misal: 0.99999).
    # Menggunakan round() memastikan kita menangkapnya dengan benar dan menghindari error.
    chosen_indices = [i for i, val in enumerate(result.x) if round(val) == 1]
    chosen_assets = [assets[i] for i in chosen_indices]
    
    return chosen_assets, result.fval

def optimize_portfolio_classical(predictions):
    """
    Mengoptimalkan portofolio menggunakan solver klasik (NumPyMinimumEigensolver)
    sebagai pembanding yang akurat.
    """
    qp = QuadraticProgram()
    for asset in predictions.index:
        qp.binary_var(name=asset)

    linear_objective = {asset: float(predictions[asset]) for asset in predictions.index if predictions[asset] > 0}
    qp.maximize(linear=linear_objective)

    all_assets = [asset for asset in predictions.index]
    qp.linear_constraint(linear={asset: 1 for asset in all_assets}, sense=">=", rhs=1, name="min_one_asset")
    qp.linear_constraint(linear={asset: 1 for asset in all_assets}, sense="<=", rhs=2, name="max_two_assets")

    classical_solver = NumPyMinimumEigensolver()
    meo = MinimumEigenOptimizer(classical_solver)
    result = meo.solve(qp)

    chosen_assets = []
    for i, var in enumerate(qp.variables):
        if result.x[i] > 0.5:
            chosen_assets.append(var.name)
    
    return chosen_assets, result