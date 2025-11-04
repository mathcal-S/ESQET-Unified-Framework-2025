#!/usr/bin/env python3
import os
import json
from dotenv import load_dotenv
from qiskit import QuantumCircuit
from qiskit_ibm_provider import IBMProvider
from qiskit.visualization import plot_histogram

# -------------------------------
# Load API Keys
# -------------------------------
load_dotenv()
IBM_TOKEN = os.getenv("IBM_Q_TOKEN_ESQET")  # or IBM_Q_TOKEN_ESQETAGI
if not IBM_TOKEN:
    raise ValueError("IBM API token not found in .env")

# -------------------------------
# Initialize Provider
# -------------------------------
provider = IBMProvider(token=IBM_TOKEN)

# Automatically pick the **fastest available real QPU**
backends = provider.backends(filters=lambda b: b.configuration().n_qubits >= 8 and not b.configuration().simulator)
if not backends:
    raise RuntimeError("No suitable QPU available. Check your IBM account.")
backend = sorted(backends, key=lambda b: b.status().pending_jobs)[0]
print(f"Using backend: {backend.name()} (pending jobs: {backend.status().pending_jobs})")

# -------------------------------
# Build 8-Qubit GHZ Circuit
# -------------------------------
num_qubits = 8
qc = QuantumCircuit(num_qubits, num_qubits)
qc.h(0)
for i in range(num_qubits - 1):
    qc.cx(i, i + 1)
qc.measure(range(num_qubits), range(num_qubits))

# -------------------------------
# Submit Job
# -------------------------------
shots = 1024
job = backend.run(qc, shots=shots)
print(f"Job submitted: {job.job_id()}")

# -------------------------------
# Wait for Completion
# -------------------------------
print("Waiting for job to finish...")
result = job.result()
counts = result.get_counts(qc)

# -------------------------------
# Compute GHZ Fidelity
# Ideal GHZ: |00000000> + |11111111>
# -------------------------------
ideal_keys = [format(0, f'0{num_qubits}b'), format(2**num_qubits - 1, f'0{num_qubits}b')]
total = sum(counts.values())
fidelity = sum(counts.get(k, 0) for k in ideal_keys) / total

# -------------------------------
# Display & Save Results
# -------------------------------
print(f"--- {num_qubits}-Qubit GHZ Circuit on {backend.name()} ---")
print(f"Counts: {counts}")
print(f"Fidelity (|00..0> + |11..1>): {fidelity:.4f}")

# Save JSON
output_data = {
    "job_id": job.job_id(),
    "backend": backend.name(),
    "counts": counts,
    "fidelity": fidelity
}
with open("ghz_ibm_results.json", "w") as f:
    json.dump(output_data, f, indent=4)

# Save histogram
plot_histogram(counts, title=f"8-Qubit GHZ on {backend.name()}").savefig("ghz_ibm_histogram.png", dpi=300)
print("Results saved: ghz_ibm_results.json, ghz_ibm_histogram.png")
