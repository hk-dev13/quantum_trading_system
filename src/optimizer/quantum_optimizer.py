# filepath: src/optimizer/quantum_optimizer.py
import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_aer.primitives import Sampler as AerSampler

def _create_objective(predictions, price_data):
    """
    Membuat fungsi objektif Markowitz (return vs risiko).
    Return: Skor prediksi (mu).
    Risiko: Matriks kovarians dari return historis (Sigma).
    q: Faktor penyeimbang antara return dan risiko.
    """
    mu = predictions.values
    returns = price_data[predictions.index].pct_change().dropna()
    
    sigma = np.zeros((len(mu), len(mu)))
    if len(returns) >= 2:
        sigma = returns.cov().values
    
    q = 0.5
    
    linear_objective = q * mu
    quadratic_objective = (1 - q) * sigma
    
    return linear_objective, quadratic_objective

def optimize_portfolio_qaoa(predictions, price_data):
    """Optimasi portofolio menggunakan QAOA dengan objektif Markowitz."""
    assets = predictions.index.tolist()
    n_assets = len(assets)
    
    linear_obj, quadratic_obj = _create_objective(predictions, price_data)

    qp = QuadraticProgram("PortfolioOptimization")
    qp.binary_var_list(n_assets, name="x")
    qp.maximize(linear=linear_obj, quadratic=-quadratic_obj)
    
    # Filter untuk aset dengan prediksi return positif teratas
    top_n = min(n_assets, 3) # Ambil 3 teratas atau kurang
    if n_assets > top_n:
        qp.linear_constraint(linear=np.ones(n_assets), sense='==', rhs=top_n, name='budget')

    sampler = AerSampler()
    optimizer = COBYLA()
    qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=1)

    optimizer_qaoa = MinimumEigenOptimizer(qaoa)
    result = optimizer_qaoa.solve(qp)
    
    chosen_indices = [i for i, val in enumerate(result.x) if round(val) == 1]
    chosen_assets = [assets[i] for i in chosen_indices]
    
    return chosen_assets, result.fval

