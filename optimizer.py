import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_aer.primitives import Sampler as AerSampler
from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver

def _create_objective(predictions, price_data):
    """
    Membuat fungsi objektif Markowitz (return vs risiko).
    Return: Skor prediksi (mu).
    Risiko: Matriks kovarians dari return historis (Sigma).
    q: Faktor penyeimbang antara return dan risiko.
    """
    mu = predictions.values
    
    # Model risiko canggih: Matriks Kovarians Historis
    returns = price_data[predictions.index].pct_change().dropna()
    
    # Gunakan matriks nol jika tidak cukup data untuk menghitung kovarians
    sigma = np.zeros((len(mu), len(mu)))
    if len(returns) >= 2:
        sigma = returns.cov().values
    
    # Kembalikan q ke 0.5 karena model risiko baru ini lebih seimbang
    q = 0.5
    
    linear_objective = q * mu
    # Bagian kuadratik dari objektif Markowitz
    quadratic_objective = (1 - q) * sigma
    
    return linear_objective, quadratic_objective

def optimize_portfolio_qaoa(predictions, price_data):
    """Optimasi portofolio menggunakan QAOA dengan objektif Markowitz."""
    assets = predictions.index.tolist()
    n_assets = len(assets)
    
    linear_obj, quadratic_obj = _create_objective(predictions, price_data)

    qp = QuadraticProgram("PortfolioOptimization")
    qp.binary_var_list(n_assets, name="x")
    # Kita memaksimalkan (Return - Risiko). Karena fungsi maximize, kita gunakan -quadratic_obj.
    qp.maximize(linear=linear_obj, quadratic=-quadratic_obj)
    
    sampler = AerSampler()
    optimizer = COBYLA()
    qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=1)

    optimizer_qaoa = MinimumEigenOptimizer(qaoa)
    result = optimizer_qaoa.solve(qp)
    
    chosen_indices = [i for i, val in enumerate(result.x) if round(val) == 1]
    chosen_assets = [assets[i] for i in chosen_indices]
    
    return chosen_assets, result.fval

def optimize_portfolio_classical(predictions, price_data):
    """Optimasi portofolio klasik dengan objektif Markowitz."""
    assets = predictions.index.tolist()
    n_assets = len(assets)

    linear_obj, quadratic_obj = _create_objective(predictions, price_data)

    qp = QuadraticProgram("PortfolioOptimization")
    qp.binary_var_list(n_assets, name="x")
    # Kita memaksimalkan (Return - Risiko). Karena fungsi maximize, kita gunakan -quadratic_obj.
    qp.maximize(linear=linear_obj, quadratic=-quadratic_obj)
    
    optimizer_classical = MinimumEigenOptimizer(NumPyMinimumEigensolver())
    result = optimizer_classical.solve(qp)
    
    chosen_indices = [i for i, val in enumerate(result.x) if round(val) == 1]
    chosen_assets = [assets[i] for i in chosen_indices]
    
    return chosen_assets, result.fval