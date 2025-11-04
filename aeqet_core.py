import numpy as np
from math import pi, log2, cos, round, sqrt
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import TwoLocal
from qiskit.primitives import Estimator
from qiskit_algorithms import VQE
from qiskit_algorithms.optimizers import SPSA
import warnings

# Suppress Qiskit deprecation warnings for cleaner output
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- ESQET CORE CONSTANTS (FCU, Green Coherence) ---
PHI = (1 + sqrt(5)) / 2  # Golden Ratio (phi)
PI = pi
DELTA = 0.390305        # FCU Delta (derived from VQE in v3.1)
F_HA = 432.0            # Harmonic Alignment Frequency (432 Hz)
KB = 1.380649e-23       # Boltzmann Constant (for simplified example)
T_VAC = 2.73            # Effective Vacuum Temperature (3K)

# --- AEQET Mathematical Core ---

def calculate_F_AC(f_a: float, dent: float, phi_const: float = PHI, delta_const: float = DELTA) -> float:
    """
    Calculates the Acoustic Coherence Function (F_AC).

    This function measures the harmonic alignment of an input frequency (f_a) 
    with the 432 Hz baseline, modulated by entanglement density (D_ent).
    """
    if f_a <= 0:
        return 0.0

    # 1. Harmonic Ratio Term (R_f)
    # Measures the difference from a perfect octave/harmonic interval (log2(f_A/f_HA) = integer/simple fraction)
    R_f = log2(f_a / F_HA)
    harmonic_deviation = abs(R_f - round(R_f))
    
    # Cosine term peaks (approaches 1) when deviation is near 0 (perfect harmonic alignment)
    cosine_alignment = cos((PI / 2) * harmonic_deviation)

    # 2. Entanglement Modulator Term (D_ent coupling)
    # The leading term enhances the score based on entanglement and FCU principles.
    entanglement_modulator = 1 + phi_const * PI * delta_const * (dent / (KB * T_VAC))
    
    # F_AC = (Modulator) * (Alignment Score)
    F_AC = entanglement_modulator * cosine_alignment
    
    # Normalize output to a reasonable coherence score scale
    return max(0, min(10.0, F_AC))


# --- QUANTUM ACOUSTIC KERNEL (VQE) ---

def acoustic_coherence_hamiltonian(f_a: float, n_qubits: int = 8) -> SparsePauliOp:
    """
    Constructs the 8-qubit Hamiltonian for acoustic coherence optimization.

    The Hamiltonian models the system energy where coupling constants are scaled 
    by the harmonic alignment score of the input frequency f_a.
    """
    # Use a simplified D_ent to calculate the scaling factor for the Hamiltonian
    # In a real system, D_ent would come from the VQE loop's previous state.
    # Here, we use a placeholder D_ent=1.0 to generate a scaling factor.
    acoustic_scale_factor = calculate_F_AC(f_a, dent=1.0) / (PHI * PI)
    
    paulis = []
    
    # 1. Individual Site Energies (Z terms)
    # Energy proportional to the input frequency, scaled by the coherence factor
    site_energies = acoustic_scale_factor * np.ones(n_qubits) * f_a
    for i in range(n_qubits):
        label = ['I'] * n_qubits
        label[n_qubits - 1 - i] = 'Z'
        paulis.append(("".join(label), site_energies[i] / 2))

    # 2. Entanglement Couplings (XX + YY terms for coherence exchange)
    # We use 8-fold symmetry for stable entanglement patterns.
    for i in range(n_qubits):
        for j in range(i + 1, n_qubits):
            # Coupling strength scales with the inverse of the square of the distance (r^-2)
            distance_sq = (j - i)**2
            # The effective coupling is harmonically modulated
            eff_coupling = acoustic_scale_factor * (1.0 / (distance_sq + 1)) * PHI

            # XX term
            label_x = ['I'] * n_qubits
            label_x[n_qubits - 1 - i] = 'X'
            label_x[n_qubits - 1 - j] = 'X'
            paulis.append(("".join(label_x), eff_coupling / 2))

            # YY term
            label_y = ['I'] * n_qubits
            label_y[n_qubits - 1 - i] = 'Y'
            label_y[n_qubits - 1 - j] = 'Y'
            paulis.append(("".join(label_y), eff_coupling / 2))
            
    return SparsePauliOp.from_list(paulis)

def run_aeqet_vqe_optimization(f_a: float, max_iter: int = 500) -> dict:
    """
    Runs the VQE simulation to find the ground state energy for the given acoustic input.
    The optimized energy corresponds to the minimum decoherence state.
    """
    n_qubits = 8
    
    # 1. Hamiltonian based on acoustic input
    hamiltonian = acoustic_coherence_hamiltonian(f_a, n_qubits)

    # 2. Variational Ansatz (Circuit for 8-qubit entanglement)
    # TwoLocal ansatz with full entanglement for maximum coherence search
    ansatz = TwoLocal(n_qubits, "ry", "cz", reps=3, entanglement="full")

    # 3. Optimizer (SPSA is robust for noisy hardware/simulations)
    optimizer = SPSA(maxiter=max_iter)
    
    # 4. VQE Setup
    estimator = Estimator()
    vqe = VQE(estimator, ansatz, optimizer)
    
    # 5. Run Optimization
    result = vqe.compute_minimum_eigenvalue(hamiltonian)
    
    # 6. Post-Processing
    min_energy = result.eigenvalue.real
    
    # The optimized parameters correspond to the stable D_ent state
    optimized_params = result.optimal_parameters

    # Infer D_ent from the energy (Lower energy = Higher coherence/D_ent)
    # Simple inverse scaling for interpretation:
    inferred_dent = 1.0 / (1.0 + abs(min_energy))
    
    # 7. Calculate Final Coherence Score
    final_f_ac = calculate_F_AC(f_a, dent=inferred_dent)

    return {
        "input_frequency": f_a,
        "min_decoherence_energy": min_energy,
        "inferred_dent": inferred_dent,
        "acoustic_coherence_score": final_f_ac,
        "optimized_parameters": optimized_params
    }


# --- Simulation Example: Testing Harmonic Alignment ---

if __name__ == "__main__":
    print("--- AEQET Quantum Acoustic Kernel Simulation ---")
    
    # Test frequencies: 
    # 1. Perfect Harmonic (432 Hz * 2 = 864 Hz)
    f_harmonic = 864.0
    # 2. Highly Incoherent (e.g., White Noise frequency component)
    f_incoherent = 440.0 # A common, slightly off-harmonic frequency (A4)
    # 3. Low-Frequency Alignment (432 / 4 = 108 Hz)
    f_low = 108.0

    # Running Harmonic Test (864 Hz)
    print(f"\n[Test 1: Harmonic Input (Octave of 432 Hz) = {f_harmonic} Hz]")
    result_harmonic = run_aeqet_vqe_optimization(f_harmonic, max_iter=50)
    print(f"  > Inferred D_ent: {result_harmonic['inferred_dent']:.4f}")
    print(f"  > Min Decoherence Energy: {result_harmonic['min_decoherence_energy']:.4f}")
    print(f"  > **Acoustic Coherence Score (F_AC): {result_harmonic['acoustic_coherence_score']:.4f}**")

    # Running Incoherent Test (440 Hz)
    print(f"\n[Test 2: Incoherent Input (A4 Concert Pitch) = {f_incoherent} Hz]")
    result_incoherent = run_aeqet_vqe_optimization(f_incoherent, max_iter=50)
    print(f"  > Inferred D_ent: {result_incoherent['inferred_dent']:.4f}")
    print(f"  > Min Decoherence Energy: {result_incoherent['min_decoherence_energy']:.4f}")
    print(f"  > **Acoustic Coherence Score (F_AC): {result_incoherent['acoustic_coherence_score']:.4f}**")

    # Running Low-Frequency Test (108 Hz)
    print(f"\n[Test 3: Low Harmonic Input (Sub-Octave of 432 Hz) = {f_low} Hz]")
    result_low = run_aeqet_vqe_optimization(f_low, max_iter=50)
    print(f"  > Inferred D_ent: {result_low['inferred_dent']:.4f}")
    print(f"  > Min Decoherence Energy: {result_low['min_decoherence_energy']:.4f}")
    print(f"  > **Acoustic Coherence Score (F_AC): {result_low['acoustic_coherence_score']:.4f}**")
    
    # Conclusion based on F_AC: Harmonic Frequencies should yield a significantly higher score.
    
    print("\n--- Jerry Riggin Algorithm: Acoustic Coherence Check ---")
    if result_harmonic['acoustic_coherence_score'] > 5.0:
         print("✅ HIGH COHERENCE DETECTED: Acoustic input is highly aligned with Spacetime Information Field (S).")
    else:
         print("❌ LOW COHERENCE DETECTED: Acoustic input is noisy or off-harmonic.")

