# Deskripsi: Algoritma untuk optimasi portofolio menggunakan metode klasik dan kuantum.
#
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
    qp = QuadraticProgram()
    for i, asset in enumerate(preds.index):
        qp.binary_var(name=asset)

    linear_objective = {asset: float(preds[asset]) for asset in preds.index if preds[asset] > 0}
    qp.maximize(linear=linear_objective)

    all_assets = [asset for asset in preds.index]
    qp.linear_constraint(linear={asset: 1 for asset in all_assets}, sense=">=", rhs=1, name="min_one_asset")
    qp.linear_constraint(linear={asset: 1 for asset in all_assets}, sense="<=", rhs=2, name="max_two_assets")
    
    sampler = AerSampler()
    optimizer = COBYLA(maxiter=100)
    qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=1)
    
    meo = MinimumEigenOptimizer(qaoa)
    result = meo.solve(qp)

    chosen_assets = []
    for i, var in enumerate(qp.variables):
        if result.x[i] > 0.5:
            chosen_assets.append(var.name)
    
    return chosen_assets, result

def optimize_portfolio_classical(preds):
    """
    Mengoptimalkan portofolio menggunakan solver klasik (NumPyMinimumEigensolver)
    sebagai pembanding yang akurat.
    """
    qp = QuadraticProgram()
    for asset in preds.index:
        qp.binary_var(name=asset)

    linear_objective = {asset: float(preds[asset]) for asset in preds.index if preds[asset] > 0}
    qp.maximize(linear=linear_objective)

    all_assets = [asset for asset in preds.index]
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