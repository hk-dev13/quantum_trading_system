import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_aer.primitives import Sampler as AerSampler
from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver

def _create_objective(predictions):
    """
    Membuat fungsi objektif yang menggabungkan return dan risiko.
    Return: Skor prediksi (mu).
    Risiko: Varians dari prediksi (sebagai diagonal dari matriks kovarians).
    q: Faktor penyeimbang antara return dan risiko.
    """
    mu = predictions.values
    
    # Model risiko sederhana: asumsikan tidak ada korelasi,
    # risiko adalah kebalikan dari skor prediksi.
    # Semakin tinggi skor, semakin rendah risiko yang diasumsikan.
    # Ini adalah proxy, bukan kovarians statistik.
    sigma = np.diag(1 / (np.abs(mu) + 1e-6)) # Matriks diagonal risiko
    
    q = 0.5  # Faktor penyeimbang. 0.5 berarti return dan risiko sama pentingnya.
    
    # Fungsi objektif: q * mu - (1-q) * diag(sigma)
    # Kita ingin memaksimalkan return (mu) dan meminimalkan risiko (sigma)
    linear_objective = q * mu
    quadratic_objective = -1 * (1 - q) * sigma # Diberi tanda negatif karena kita memaksimalkan
    
    return linear_objective, quadratic_objective

def optimize_portfolio_qaoa(predictions):
    """Optimasi portofolio menggunakan QAOA dengan objektif return-vs-risiko."""
    assets = predictions.index.tolist()
    n_assets = len(assets)
    
    linear_obj, quadratic_obj = _create_objective(predictions)

    qp = QuadraticProgram("PortfolioOptimization")
    qp.binary_var_list(n_assets, name="x")
    qp.maximize(linear=linear_obj, quadratic=quadratic_obj)
    
    sampler = AerSampler()
    optimizer = COBYLA()
    qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=1)

    optimizer_qaoa = MinimumEigenOptimizer(qaoa)
    result = optimizer_qaoa.solve(qp)
    
    chosen_indices = [i for i, val in enumerate(result.x) if round(val) == 1]
    chosen_assets = [assets[i] for i in chosen_indices]
    
    return chosen_assets, result.fval

def optimize_portfolio_classical(predictions):
    """Optimasi portofolio klasik dengan objektif return-vs-risiko."""
    assets = predictions.index.tolist()
    n_assets = len(assets)

    linear_obj, quadratic_obj = _create_objective(predictions)

    qp = QuadraticProgram("PortfolioOptimization")
    qp.binary_var_list(n_assets, name="x")
    qp.maximize(linear=linear_obj, quadratic=quadratic_obj)
    
    optimizer_classical = MinimumEigenOptimizer(NumPyMinimumEigensolver())
    result = optimizer_classical.solve(qp)
    
    chosen_indices = [i for i, val in enumerate(result.x) if round(val) == 1]
    chosen_assets = [assets[i] for i in chosen_indices]
    
    return chosen_assets, result.fval