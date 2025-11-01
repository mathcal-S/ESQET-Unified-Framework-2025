from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.circuit import Parameter
from qiskit_aer import AerSimulator
from qiskit.quantum_info import Operator, state_fidelity
from qiskit_ibm_runtime import QiskitRuntimeService, Estimator, Session, Options
from qiskit.primitives import Estimator as PrimitiveEstimator
from scipy.optimize import minimize
import numpy as np
import os

# ESQET Constants
PHI = (1 + np.sqrt(5)) / 2
PI = np.pi
DELTA = 1e-18
D_OBS = 0.8  # High coherence

def add_variational_layer(circuit, qubits, theta, phi):
    """Adds variational layer with RY, RZ, CNOT."""
    for i in qubits:
        circuit.ry(theta, i)
        circuit.rz(phi, i)
    for i in range(len(qubits) - 1):
        circuit.cx(qubits[i], qub_bits[i + 1])

def omni_one_kernel_variational(n_qubits=5, phase_negfib=5, delta=0.5, layers=2, measure_all=True):
    """Variational quantum circuit for ESQET coherence sim."""
    if n_qubits < 5:
        raise ValueError("Minimum 5 qubits required.")
    
    qr = QuantumRegister(n_qubits, 'q')
    cr = ClassicalRegister(n_qubits, 'c') if measure_all else None
    circuit = QuantumCircuit(qr, cr) if measure_all else QuantumCircuit(qr)

    theta = Parameter('θ')
    phi = Parameter('φ')
    params = [theta, phi]

    # Superposition
    circuit.h(range(n_qubits))

    # FCU Phase
    circuit.rz(theta * phase_negfib * PI, 0)

    # Entanglement Chain
    for i in range(n_qubits - 1):
        circuit.cx(i, i + 1)

    # QKD-like
    circuit.h(0)
    circuit.cx(0, 1)

    # Coherence Feedback
    circuit.crz(phi * np.cos(delta * phase_negfib), 2, 3)

    # Black Hole Reset
    circuit.h(4)
    circuit.cswap(4, 2, 3)

    # Variational Layers
    for layer in range(layers):
        layer_theta = Parameter(f'θ_{layer}')
        layer_phi = Parameter(f'φ_{layer}')
        params += [layer_theta, layer_phi]
        add_variational_layer(circuit, range(n_qubits), layer_theta, layer_phi)

    if measure_all:
        circuit.measure(qr, cr)

    return circuit, params

def orch_or_hamiltonian(n_qubits, g=1.0):
    """Orch-OR Hamiltonian: ZZ chain + X field + FCU Z."""
    paulis = []
    for i in range(n_qubits - 1):
        label = ['I'] * n_qubits
        label[i] = 'Z'
        label[i+1] = 'Z'
        paulis.append((''.join(label), 1.0))
    for i in range(n_qubits):
        label = ['I'] * n_qubits
        label[i] = 'X'
        paulis.append((''.join(label), g))
    label = ['Z'] * n_qubits
    paulis.append((''.join(label), PHI * PI * DELTA * D_OBS))
    return SparsePauliOp.from_list(paulis)

def cost_function(params, circuit, params_list, H, backend, shots=1024):
    """VQE cost: <H> via shots."""
    param_dict = dict(zip(params_list, params))
    bound_circuit = circuit.assign_parameters(param_dict)
    result = execute(bound_circuit, backend, shots=shots).result()
    counts = result.get_counts()
    expectation = 0
    for state, count in counts.items():
        state_vec = np.zeros(2**bound_circuit.num_qubits)
        state_vec[int(state, 2)] = 1
        expectation += count / shots * np.real(np.dot(state_vec.T.conj(), H.to_matrix() @ state_vec))
    return expectation

def get_backend(simulator=True, noisy=False):
    """Backend: Aer or IBM Runtime."""
    if simulator:
        backend = AerSimulator()
    else:
        service = QiskitRuntimeService(channel="ibm_quantum")  # Token in env
        backend = service.least_busy(min_num_qubits=5)
    if noisy:
        from qiskit_aer.noise import NoiseModel, depolarizing_error
        noise_model = NoiseModel()
        error_1q = depolarizing_error(0.01, 1)
        error_2q = depolarizing_error(0.05, 2)
        noise_model.add_all_qubit_quantum_error(error_1q, ['h', 'ry', 'rz', 'crz'])
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'cswap'])
        return backend, noise_model
    return backend, None

def run_vqe(n_qubits=5, layers=2, maxiter=50):
    """Full VQE Run: Sim/Hardware."""
    circuit, params = omni_one_kernel_variational(n_qubits, layers=layers, measure_all=True)
    H = orch_or_hamiltonian(n_qubits)
    backend, noise = get_backend(simulator=True, noisy=True)  # Sim first; set False for IBM

    # Initial params scaled by D_obs
    initial_params = np.random.uniform(-np.pi, np.pi, len(params)) * D_OBS

    # Callback for progress
    def callback(res):
        print(f"🔹 Iteration {len(res)}: Cost {res.fun:.4f}")

    # Minimize
    result = minimize(cost_function, initial_params, args=(circuit, params, H, backend, 1024), method='COBYLA', callback=callback, options={'maxiter': maxiter})

    # Optimized sim
    opt_circuit = circuit.assign_parameters(dict(zip(params, result.x)))
    opt_results = execute(opt_circuit, backend, shots=1024).result()
    counts = opt_results.get_counts()

    # Fidelity to ground (proxy)
    ground_fidelity = 1 - result.fun / n_qubits  # Simplified

    print(f"🔹 Optimized Cost: {result.fun:.4f}")
    print(f"🔹 Ground Fidelity: {ground_fidelity:.4f}")
    print(f"🔹 Counts: {counts}")

    # For IBM Hardware (10-min window)
    if not simulator:
        with Session(service=service, backend=backend) as session:
            estimator = Estimator(session=session)
            # Batch run (limit to 50 iters for time)
            opt_result = minimize(cost_function, initial_params[:4], args=(circuit, params[:4], H, estimator, 512), method='COBYLA', options={'maxiter': 50})
        print(f"🔹 Hardware Cost: {opt_result.fun:.4f}")

    return result

# Run (Sim first; set simulator=False for IBM)
if __name__ == "__main__":
    result = run_vqe(n_qubits=5, layers=2, maxiter=50)
