#!/usr/bin/env python3
import numpy as np
from functools import reduce
import json
from datetime import datetime
import matplotlib.pyplot as plt

def run_ghz_circuit(num_qubits=2, shots=1024, noise_prob=0.01, relaxation_time=50e-6, t_gate=20e-9):
    if num_qubits < 2 or num_qubits > 16:
        raise ValueError("Number of qubits must be between 2 and 16.")
    
    # --- 1. Create Ideal Statevector (H on 0, CNOT chain) ---
    # Basis: |0> = [1,0], |1> = [0,1]
    H = (1/np.sqrt(2)) * np.array([[1, 1], [1, -1]])  # Hadamard
    CNOT = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])  # CNOT control-target
    I = np.eye(2)
    
    # Initial |000...>
    state = np.zeros(2**num_qubits, dtype=complex)
    state[0] = 1.0
    
    # Apply H on qubit 0 (MSB)
    state = np.kron(H, np.eye(2**(num_qubits-1))) @ state
    
    # Entangle chain (CNOT i to i+1, for i=0 to n-2)
    for i in range(num_qubits - 1):
        # CNOT on qubits i (control) and i+1 (target); others I
        # Left: I^i
        if i == 0:
            left = np.eye(1)
        else:
            left = reduce(np.kron, [I] * i)
        # Right: I^(n-i-2)
        if num_qubits - i - 2 == 0:
            right = np.eye(1)
        else:
            right = reduce(np.kron, [I] * (num_qubits - i - 2))
        cnot_full = np.kron(np.kron(left, CNOT), right)
        state = cnot_full @ state
    
    # Ideal GHZ: (|0...0> + |1...1>)/sqrt(2)
    ideal_state = np.zeros(2**num_qubits, dtype=complex)
    ideal_state[0] = 1/np.sqrt(2)
    ideal_state[-1] = 1/np.sqrt(2)
    
    # --- 2. Add Noise: Depolarizing on Gates + Thermal Relaxation ---
    # Depolarizing (per gate; prob = error rate)
    def depolarize(state, p):
        if np.random.rand() < p:
            # Random Pauli: I, X, Y, Z with equal prob
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
        return state / np.linalg.norm(state)  # Renorm
    
    # Thermal relaxation (amplitude damping per qubit per gate time)
    gamma = 1 / relaxation_time  # Decay rate
    def thermal_relax(state, dt):
        for q in range(num_qubits):
            # Damping on qubit q (simplified single-qubit Kraus)
            p_ground = np.exp(-gamma * dt)
            E0 = np.sqrt(p_ground) * np.array([[1, 0], [0, 0]])  # |0><0|
            E1 = np.array([[0, np.sqrt(1-p_ground)], [0, 1]])  # |1><1| + leak
            # Embed in full space
            if q == 0:
                left = np.eye(1)
            else:
                left = reduce(np.kron, [I] * q)
            if num_qubits - q - 1 == 0:
                right = np.eye(1)
            else:
                right = reduce(np.kron, [I] * (num_qubits - q - 1))
            E0_full = np.kron(np.kron(left, E0), right)
            E1_full = np.kron(np.kron(left, E1), right)
            state = E0_full @ state + E1_full @ state
        return state / np.linalg.norm(state)
    
    # Apply noise to H + each CNOT (num_qubits gates total)
    state = depolarize(state, noise_prob)  # H noise
    state = thermal_relax(state, t_gate)
    for i in range(num_qubits - 1):
        state = depolarize(state, noise_prob)  # CNOT noise
        state = thermal_relax(state, t_gate)
    
    # --- 3. Simulate Measurement (project to Z-basis + bit-flip noise)
    probs = np.abs(state)**2
    meas_prob = 0.005  # Bit-flip rate
    counts = {}
    for _ in range(shots):
        outcome = np.random.choice(2**num_qubits, p=probs)
        bitstring = format(outcome, f'0{num_qubits}b')
        # Flip bits with prob
        for b in range(num_qubits):
            if np.random.rand() < meas_prob:
                bitstring = bitstring[:b] + ('1' if bitstring[b]=='0' else '0') + bitstring[b+1:]
        counts[bitstring] = counts.get(bitstring, 0) + 1
    
    # --- 4. Fidelity (overlap with ideal GHZ probs)
    ideal_probs = np.abs(ideal_state)**2
    measured_probs = np.array([counts.get(format(i, f'0{num_qubits}b'), 0) / shots for i in range(2**num_qubits)])
    fidelity = np.sum(np.sqrt(ideal_probs * measured_probs)) ** 2  # Uhlmann fidelity
    
    # Print
    print(f"--- {num_qubits}-Qubit GHZ Circuit (Noisy) ---")
    print("H(0); CNOT(0,1); CNOT(1,2); ... CNOT(n-2,n-1); Measure all")
    print("-" * 40)
    print(f"--- Counts ({shots} shots, noise_prob={noise_prob}) ---")
    for bitstring, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]:  # Top 10
        print(f"{bitstring}: {count}")
    
    print(f"\nFidelity (GHZ overlap): {fidelity:.4f}")
    
    # Plot histogram
    plt.figure(figsize=(10, 6))
    plt.bar(counts.keys(), counts.values())
    plt.xlabel('Bitstring')
    plt.ylabel('Counts')
    plt.title(f'Noisy GHZ {num_qubits} Qubits (Fidelity: {fidelity:.4f})')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('ghz_noisy_histogram.png', dpi=300)
    plt.show()
    
    # JSON
    data = {"num_qubits": num_qubits, "shots": shots, "noise_prob": noise_prob, "fidelity": float(fidelity), "counts": counts}
    with open('ghz_results.json', 'w') as f:
        json.dump(data, f, indent=4)
    
    return counts, fidelity

# Example Usage
if __name__ == "__main__":
    counts, fidelity = run_ghz_circuit(num_qubits=8, shots=1024, noise_prob=0.01, relaxation_time=50e-6, t_gate=20e-9)
