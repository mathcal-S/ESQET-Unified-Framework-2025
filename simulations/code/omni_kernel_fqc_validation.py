#!/usr/bin/env python3
import os
import json
import numpy as np
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import Pauli, SparsePauliOp
from qiskit.algorithms.minimum_eigensolvers import VQE
from qiskit.algorithms.optimizers import COBYLA
from qiskit.providers.aer import AerSimulator
from qiskit_ibm_runtime import Estimator
from dotenv import load_dotenv

# Load IBM Token (not used for simulator but for consistency)
load_dotenv(os.path.expanduser("~/vessel_agi/.env"))
IBM_TOKEN = os.getenv("IBM_TOKEN")

# Parameters
N_QUBITS = 5
LAYERS = 2
MAX_ITER = 20
OUTPUT_FILE = "qpu_vqe_results.json"
LATEX_FILE = "fqc_table.tex"

# ESQET Hamiltonian
def create_esqet_hamiltonian(n_qubits: int):
    pauli_list = [
        (Pauli('IIIIZ'), 1.0),
        (Pauli('IIZII'), -0.5),
        (Pauli('IZIZI'), 0.2),
        (Pauli('ZIIII'), 0.1),
        (Pauli('ZZZII'), -0.9),
        (Pauli('XXXXX'), 0.05)
    ]
    op = sum([SparsePauliOp(p, c) for p, c in pauli_list])
    return op.apply_layout(list(range(n_qubits)))

# Run VQE validation
def run_validation():
    print("🔬 Running ESQET F_QC validation on AerSimulator...")
    hamiltonian = create_esqet_hamiltonian(N_QUBITS)
    ansatz = EfficientSU2(N_QUBITS, reps=LAYERS, entanglement="linear")
    optimizer = COBYLA(maxiter=MAX_ITER)
    
    # Simulator
    simulator = AerSimulator()
    estimator = Estimator()
    vqe = VQE(ansatz=ansatz, optimizer=optimizer, estimator=estimator)
    
    result = vqe.compute_minimum_eigensolution(hamiltonian)
    
    # Save JSON
    min_energy = result.eigenvalue.real
    final_data = {
        "esqet_f_qc_score": min_energy,
        "backend": "AerSimulator",
        "vqe_iterations": MAX_ITER,
        "ansatz_layers": LAYERS,
        "optimal_parameters": {str(k): float(v) for k, v in result.optimal_parameters.items()}
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(final_data, f, indent=4)
    
    # Generate LaTeX table
    latex_content = f"""
\\begin{{table}}[h!]
\\centering
\\begin{{tabular}}{{|c|c|}}
\\hline
\\textbf{{Metric}} & \\textbf{{Value}} \\\\
\\hline
ESQET F\\_QC Score & {min_energy:.6f} \\\\
Backend Used & AerSimulator \\\\
VQE Iterations & {MAX_ITER} \\\\
Ansatz Layers & {LAYERS} \\\\
\\hline
\\end{{tabular}}
\\caption{{Simulator-based validation of ESQET Hamiltonian (proxy F\\_QC score).}}
\\end{{table}}
"""
    with open(LATEX_FILE, "w") as f:
        f.write(latex_content)
    
    print(f"✅ Validation complete! ESQET F_QC score: {min_energy:.6f}")
    print(f"💾 JSON saved to: {OUTPUT_FILE}")
    print(f"💾 LaTeX table saved to: {LATEX_FILE}")
    
    return final_data

if __name__ == "__main__":
    run_validation()
