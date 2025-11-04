#!/usr/bin/env python3
import numpy as np
from functools import reduce
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Pauli matrices for noise
X = np.array([[0, 1], [1, 0]])
Y = np.array([[0, -1j], [1j, 0]])
Z = np.array([[1, 0], [0, -1]])

def kron_multi(mats):
    """Safe kron reduce with identity fallback"""
    if len(mats) == 0:
        return np.array([[1]])
    return reduce(np.kron, mats)

def run_ghz_circuit(num_qubits=2, shots=1024, noise_prob=0.01, relaxation_time=50e-6, t_gate=20e-9):
    if num_qubits < 2 or num_qubits > 16:
        raise ValueError("Number of qubits must be between 2 and 16.")
    
    # --- 1. Create Ideal Statevector (H on 0, CNOT chain) ---
    H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]])
    CNOT = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0],
                     [0, 0, 0, 1],
                     [0, 0, 1, 0]])
    I = np.eye(2)
    
    # Initial |000...0>
    state = np.zeros(2**num_qubits, dtype=complex)
    state[0] = 1.0
    
    # Apply H on qubit 0 (MSB)
    state = np.kron(H, np.eye(2**(num_qubits-1))) @ state
    
    # Entangle chain (CNOT i->i+1)
    for i in range(num_qubits - 1):
        left = kron_multi([I] * i)
        right = kron_multi([I] * (num_qubits - i - 2))
        cnot_full = np.kron(np.kron(left, CNOT), right)
        state = cnot_full @ state
    
    # Ideal GHZ state
    ideal_state = np.zeros(2**num_qubits, dtype=complex)
    ideal_state[0] = 1/np.sqrt(2)
    ideal_state[-1] = 1/np.sqrt(2)
    
    # --- 2. Noise: Depolarizing + Thermal Relaxation ---
    gamma = 1 / relaxation_time
    
    def depolarize(state, p):
        if np.random.rand() < p:
            pauli_choice = np.random.choice(['I', 'X', 'Y', 'Z'])
            if pauli_choice == 'X':
                op = np.kron(X, np.eye(2**(num_qubits-1)))
            elif pauli_choice == 'Y':
                op = np.kron(Y, np.eye(2**(num_qubits-1)))
            elif pauli_choice == 'Z':
                op = np.kron(Z, np.eye(2**(num_qubits-1)))
            else:
                op = np.eye(2**num_qubits)
            state = op @ state
        return state / np.linalg.norm(state)
    
    def thermal_relax(state, dt):
        for q in range(num_qubits):
            p_ground = np.exp(-gamma * dt)
            E0 = np.sqrt(p_ground) * np.array([[1, 0], [0, 0]])
            E1 = np.array([[0, np.sqrt(1-p_ground)], [0, 1]])
            left = kron_multi([I] * q)
            right = kron_multi([I] * (num_qubits - q - 1))
            E0_full = np.kron(np.kron(left, E0), right)
            E1_full = np.kron(np.kron(left, E1), right)
            state = E0_full @ state + E1_full @ state
        return state / np.linalg.norm(state)
    
    # Apply noise to H + CNOTs
    state = depolarize(state, noise_prob)
    state = thermal_relax(state, t_gate)
    for _ in range(num_qubits - 1):
        state = depolarize(state, noise_prob)
        state = thermal_relax(state, t_gate)
    
    # --- 3. Simulate Measurement ---
    probs = np.abs(state)**2
    meas_prob = 0.005  # bit-flip rate
    counts = {}
    for _ in range(shots):
        outcome = np.random.choice(2**num_qubits, p=probs)
        bitstring = format(outcome, f'0{num_qubits}b')
        # Bit-flip noise
        bitstring = ''.join(
            ('1' if b=='0' else '0') if np.random.rand() < meas_prob else b
            for b in bitstring
        )
        counts[bitstring] = counts.get(bitstring, 0) + 1
    
    # --- 4. Fidelity ---
    measured_probs = np.array([counts.get(format(i, f'0{num_qubits}b'), 0)/shots for i in range(2**num_qubits)])
    ideal_probs = np.abs(ideal_state)**2
    fidelity = np.sum(np.sqrt(ideal_probs * measured_probs)) ** 2
    
    # Print results
    print(f"--- {num_qubits}-Qubit GHZ Circuit (Noisy) ---")
    print("H(0); CNOT chain; Measure all")
    print("-"*40)
    print(f"--- Counts ({shots} shots) ---")
    for bitstring, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{bitstring}: {count}")
    print(f"\nFidelity: {fidelity:.4f}")
    
    # Plot histogram
    plt.figure(figsize=(10,6))
    plt.bar(counts.keys(), counts.values())
    plt.xlabel('Bitstring')
    plt.ylabel('Counts')
    plt.title(f'Noisy GHZ {num_qubits} Qubits (Fidelity: {fidelity:.4f})')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('ghz_noisy_histogram.png', dpi=300)
    plt.show()
    
    # Save JSON
    data = {"num_qubits": num_qubits, "shots": shots, "noise_prob": noise_prob, "fidelity": float(fidelity), "counts": counts}
    with open('ghz_results.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    return counts, fidelity

if __name__ == "__main__":
    counts, fidelity = run_ghz_circuit(num_qubits=8, shots=1024, noise_prob=0.01)
