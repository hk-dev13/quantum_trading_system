# filepath: src/optimizer/quantum_optimizer.py
import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit_aer.primitives import Sampler as AerSampler

def _create_markowitz_objective(predictions, price_data, q_factor):
    """
    Create Markowitz objective function (return vs risk).
    q_factor is now accepted as an argument.
    """
    mu = predictions.values
    
    returns = price_data[predictions.index].pct_change().dropna()
    
    sigma = np.zeros((len(mu), len(mu)))
    if len(returns) >= 2:
        sigma = returns.cov().values
    
    linear_objective = q_factor * mu
    quadratic_objective = (1 - q_factor) * sigma
    
    return linear_objective, quadratic_objective

def optimize_portfolio_qaoa(predictions, price_data, q_factor):
    """
    Portfolio optimization using QAOA with Markowitz objective.
    This function now accepts q_factor.
    """
    assets = predictions.index.tolist()
    n_assets = len(assets)
    
    linear_obj, quadratic_obj = _create_markowitz_objective(predictions, price_data, q_factor)

    qp = QuadraticProgram("PortfolioOptimization")
    qp.binary_var_list(n_assets, name="x")
    qp.maximize(linear=linear_obj, quadratic=-quadratic_obj)
    
    sampler = AerSampler()
    optimizer = COBYLA()
    qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=1)

    optimizer_qaoa = MinimumEigenOptimizer(qaoa)
    result = optimizer_qaoa.solve(qp)
    
    chosen_indices = [i for i, val in enumerate(result.x) if round(val) == 1]
    chosen_assets = [assets[i] for i in chosen_indices]
    
    return chosen_assets

