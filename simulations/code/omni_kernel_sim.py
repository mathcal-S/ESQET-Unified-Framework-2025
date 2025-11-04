from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, execute
from qiskit.circuit import Parameter
from qiskit.visualization import plot_histogram, circuit_drawer
from qiskit.quantum_info import Operator, state_fidelity
from scipy.optimize import minimize
import numpy as np
import matplotlib.pyplot as plt

def add_variational_layer(circuit, qubits, theta, phi):
    """Adds a single variational layer with RY, RZ, and CNOT gates."""
    for i in qubits:
        circuit.ry(theta, i)
        circuit.rz(phi, i)
    for i in range(len(qubits) - 1):
        circuit.cx(qubits[i], qubits[i + 1])

def omni_one_kernel_variational(n_qubits=5, phase_negfib=5, delta=0.5, layers=1, measure_all=False):
    """Constructs a variational quantum circuit with layered parameterization."""
    if n_qubits < 5:
        raise ValueError("Minimum 5 qubits required for black hole reset operation.")

    qr = QuantumRegister(n_qubits, 'q')
    cr = ClassicalRegister(n_qubits, 'c') if measure_all else None
    circuit = QuantumCircuit(qr, cr) if measure_all else QuantumCircuit(qr)

    # Parameterized angles for core circuit
    theta = Parameter('θ')
    phi = Parameter('φ')
    parameters = [theta, phi]

    # Step 1: Superposition
    circuit.h(range(n_qubits))

    # Step 2: Parameterized phase encoding
    circuit.rz(theta * phase_negfib * np.pi, 0)

    # Step 3: Linear entanglement chain
    for i in range(n_qubits - 1):
        circuit.cx(i, i + 1)

    # Step 4: QKD-like operations
    circuit.h(0)
    circuit.cx(0, 1)

    # Step 5: Parameterized coherence feedback
    pi_sq = np.pi ** 2
    circuit.crz(phi * np.cos(delta * phase_negfib), 2, 3)

    # Step 6: Black hole reset analogue
    circuit.h(4)
    circuit.cswap(4, 2, 3)

    # Step 7: Add variational layers
    for layer in range(layers):
        layer_theta = Parameter(f'θ_{layer}')
        layer_phi = Parameter(f'φ_{layer}')
        parameters.extend([layer_theta, layer_phi])
        add_variational_layer(circuit, range(n_qubits), layer_theta, layer_phi)

    if measure_all:
        circuit.measure(qr, cr)

    return circuit, parameters

def cost_function(params, circuit, parameters, target_operator, backend, shots=1024):
    """Computes the expectation value of a target operator for VQE."""
    param_dict = {p: v for p, v in zip(parameters, params)}
    bound_circuit = circuit.assign_parameters(param_dict)
    result = execute(bound_circuit, backend, shots=shots).result()
    counts = result.get_counts()

    expectation = 0
    for state, count in counts.items():
        state_vec = np.zeros(2**bound_circuit.num_qubits)
        state_vec[int(state, 2)] = 1
        expectation += count * np.real(np.dot(state_vec.T, np.dot(target_operator.data, state_vec)))
    return expectation / shots

def get_backend(backend_type='statevector', noisy=False):
    """Returns a Qiskit backend with optional noise model."""
    if backend_type not in ['statevector', 'qasm']:
        raise ValueError("backend_type must be 'statevector' or 'qasm'.")

    backend = Aer.get_backend(f'{backend_type}_simulator')
    if noisy and backend_type == 'qasm':
        noise_model = NoiseModel()
        error_1q = depolarizing_error(0.01, 1)
        error_2q = depolarizing_error(0.05, 2)
        noise_model.add_all_qubit_quantum_error(error_1q, ['h', 'ry', 'rz', 'crz'])
        noise_model.add_all_qubit_quantum_error(error_2q, ['cx', 'cswap'])
        return backend, noise_model
    return backend, None

def simulate_circuit(circuit, backend_type='statevector', noisy=False, shots=1024, callback=None):
    """Simulates the quantum circuit with optional noise and callback."""
    backend, noise_model = get_backend(backend_type, noisy)
    try:
        result = execute(circuit, backend, shots=shots, noise_model=noise_model).result()
        if callback:
            callback(result)
        if backend_type == 'statevector':
            statevector = result.get_statevector()
            prob_sum = np.sum(np.abs(statevector)**2)
            return {
                'statevector': statevector,
                'amplitudes': np.abs(statevector)[:10],
                'prob_sum': prob_sum
            }
        else:
            counts = result.get_counts()
            return {'counts': counts}
    except Exception as err:
        return {'error': str(err)}

def compare_statevectors(state1, state2):
    """Computes the fidelity between two statevectors."""
    return state_fidelity(state1, state2)

def visualize_results(circuit, results, backend_type='statevector', save_qasm=False, qasm_filename='omni_kernel.qasm'):
    """Visualizes circuit, statevector, or measurement results."""
    if 'error' in results:
        print(f"❌ Simulation failed: {results['error']}")
        return

    # Export to OpenQASM if requested
    if save_qasm:
        circuit.qasm(filename=qasm_filename)
        print(f"🔹 OpenQASM exported to {qasm_filename}")

    # Plot circuit diagram
    print("\n🔹 Circuit Diagram:")
    print(circuit_drawer(circuit, output='text'))

    if backend_type == 'statevector':
        print("🔹 First 10 amplitudes (abs):", results['amplitudes'])
        print(f"🔹 Probability sum (should be ≈ 1): {results['prob_sum']:.4f}")
        
        plt.figure(figsize=(10, 6))
        plot_state_city(results['statevector'], title="Statevector City Plot")
        plt.show()
        
        plt.figure(figsize=(10, 6))
        plot_bloch_multivector(results['statevector'], title="Bloch Sphere Representation")
        plt.show()
    else:
        print("🔹 Measurement counts:", results['counts'])
        plt.figure(figsize=(10, 6))
        plot_histogram(results['counts'], title="Measurement Histogram")
        plt.show()

if __name__ == "__main__":
    # Create variational circuit with 2 layers
    circuit, params = omni_one_kernel_variational(n_qubits=5, phase_negfib=5, delta=0.5, layers=2, measure_all=True)
    
    # Define a simple target operator (ZZZZZ Hamiltonian)
    target_operator = Operator(np.diag([1 if bin(i).count('1') % 2 == 0 else -1 for i in range(2**5)]))

    # Callback for logging optimization progress
    def optimization_callback(result):
        counts = result.get_counts()
        print(f"🔹 Intermediate counts: {counts}")

    # Simulate with statevector (no measurements)
    circuit_statevector = omni_one_kernel_variational(n_qubits=5, phase_negfib=5, delta=0.5, layers=2, measure_all=False)[0]
    initial_params = [0.5, np.pi**2] + [0.1, 0.2] * 2  # Parameters for core + 2 layers
    circuit_statevector = circuit_statevector.assign_parameters({p: v for p, v in zip(params, initial_params)})
    results_statevector = simulate_circuit(circuit_statevector, backend_type='statevector')
    visualize_results(circuit_statevector, results_statevector, backend_type='statevector', save_qasm=True)

    # Simulate with QASM and noise
    results_qasm = simulate_circuit(circuit.assign_parameters({p: v for p, v in zip(params, initial_params)}),
                                   backend_type='qasm', noisy=True, shots=1024, callback=optimization_callback)
    visualize_results(circuit, results_qasm, backend_type='qasm')

    # Compare statevectors (ideal vs noisy simulation)
    circuit_noisy = circuit.assign_parameters({p: v for p, v in zip(params, initial_params)})
    results_noisy = simulate_circuit(circuit_noisy, backend_type='statevector', noisy=True)
    if 'statevector' in results_statevector and 'statevector' in results_noisy:
        fidelity = compare_statevectors(results_statevector['statevector'], results_noisy['statevector'])
        print(f"🔹 Fidelity between ideal and noisy statevectors: {fidelity:.4f}")

    # Variational optimization with COBYLA
    backend, _ = get_backend('qasm')
    result = minimize(
        cost_function,
        initial_params,
        args=(circuit, params, target_operator, backend, 1024),
        method='COBYLA',
        options={'maxiter': 100}
    )
    print(f"\n🔹 Optimized parameters: {result.x}")
    print(f"🔹 Optimized cost: {result.fun}")

    # Simulate with optimized parameters
    optimized_circuit = circuit.assign_parameters({p: v for p, v in zip(params, result.x)})
    results_optimized = simulate_circuit(optimized_circuit, backend_type='qasm', noisy=True, shots=1024, callback=optimization_callback)
    visualize_results(optimized_circuit, results_optimized, backend_type='qasm')
