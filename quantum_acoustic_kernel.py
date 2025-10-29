import numpy as np
from qiskit.quantum_info import Pauli, SparsePauliOp
from qiskit.circuit.library import EfficientSU2
from qiskit.algorithms.minimum_eigensolvers import VQE
from qiskit.algorithms.optimizers import SPSA
from qiskit.primitives import Estimator
from typing import List

# --- ESQET QAK Constants ---
N_QUBITS: int = 8
PHI: float = (1 + np.sqrt(5)) / 2 # Golden Ratio (for harmonic targets)
F_CENTER: float = 432.0          # Hz (The Phi-harmonic baseline)
E_MAX: float = 1.0               # Maximum theoretical Dissonance Score (for normalization)
ALPHA_AC: float = 0.85           # Dimensionless coupling strength (alpha_AC in F_AC equation)
F_SCHUMANN: float = 7.83         # Hz (Schumann Resonance)

def get_harmonic_target(q_idx_1: int, q_idx_2: int) -> float:
    """Calculates the target Phi-harmonic ratio (R_target) between two qubits."""
    # A simplified model using basic harmonic ratios and Phi-scaling for the 8-qubit register
    # Target ratios include Octaves (1/2), Perfect Fifths (2/3), and Fourths (3/4).
    # We apply a slight Phi-scaling to the perfect fifth (2/3 * Phi_factor) to favor the 432 Hz tuning.
    
    # Example Target Ratios (Simplified for demonstration):
    ratios = {
        (0, 4): 2.0,      # Octave (2:1)
        (0, 3): 1.5 * (1.0/PHI), # Phi-scaled Perfect Fifth (3:2)
        (0, 2): 1.333,    # Perfect Fourth (4:3)
        # Add more complex Phi-scaled ratios for a full 8-qubit model...
    }
    
    # Look up the target ratio or return the inverse if indices are swapped
    key = tuple(sorted((q_idx_1, q_idx_2)))
    if key in ratios:
        return ratios[key] if q_idx_1 < q_idx_2 else 1.0 / ratios[key]
    
    # Default non-harmonic coupling for all other pairs
    return 1.0 

def create_acoustic_hamiltonian(acoustic_spectrum: List[float]) -> SparsePauliOp:
    """
    Constructs the QAK Hamiltonian (H_Acoustic) based on the input acoustic spectrum.

    The Hamiltonian measures the difference (dissonance) between the actual frequency 
    ratios and the target Phi-harmonic ratios.

    H_Acoustic = sum(lambda_i * Z_i) + sum(J_ij * X_i X_j + K_ij * Y_i Y_j)
    """
    if len(acoustic_spectrum) != N_QUBITS:
        raise ValueError(f"Acoustic spectrum must have {N_QUBITS} components.")

    pauli_list = []

    # 1. Single-qubit Terms (lambda_i * Z_i) - Encode spectral intensity
    # lambda_i (coefficient) is the spectral intensity (normalized by max intensity)
    max_intensity = max(acoustic_spectrum) if max(acoustic_spectrum) > 0 else 1.0
    for i, intensity in enumerate(acoustic_spectrum):
        lambda_i = intensity / max_intensity
        pauli_list.append((Pauli(f'Z{i}'), lambda_i * 0.1)) # Small weight on single-qubit terms

    # 2. Two-qubit Coupling Terms (J_ij * X_i X_j + K_ij * Y_i Y_j) - Encode dissonance
    for i in range(N_QUBITS):
        for j in range(i + 1, N_QUBITS):
            # Calculate the actual frequency ratio relative to 432 Hz
            f_i = acoustic_spectrum[i] * F_CENTER # Assumes spectrum list is relative scaling factors
            f_j = acoustic_spectrum[j] * F_CENTER
            
            if f_j == 0: continue # Avoid division by zero
            R_actual = f_i / f_j
            
            # Target Phi-harmonic ratio
            R_target = get_harmonic_target(i, j)
            
            # The coupling strength J_ij/K_ij is the DISSONANCE magnitude
            dissonance = abs(R_actual - R_target)
            
            # Coupling coefficient (Scaled Dissonance)
            J_ij = dissonance * 0.5
            K_ij = dissonance * 0.5
            
            pauli_list.append((Pauli(f'X{i}X{j}'), J_ij))
            pauli_list.append((Pauli(f'Y{i}Y{j}'), K_ij))
            
    # Combine terms into a SparsePauliOp (the Hamiltonian)
    H_acoustic = SparsePauliOp.from_list(pauli_list)
    return H_acoustic

def run_qak_vqe(H_acoustic: SparsePauliOp) -> float:
    """
    Runs the VQE algorithm to find the minimum eigenvalue E_min.
    """
    # 1. Ansatz (Trial Wave Function)
    # Using the hardware-efficient EfficientSU2, optimized for entanglement
    ansatz = EfficientSU2(H_acoustic.num_qubits, entanglement='linear', reps=3)
    
    # 2. Optimizer
    # Using SPSA (Simultaneous Perturbation Stochastic Approximation) for fast convergence
    optimizer = SPSA(maxiter=100)
    
    # 3. Estimator (for calculating expectation values)
    estimator = Estimator()
    
    # 4. VQE Setup and Execution
    vqe = VQE(estimator, ansatz, optimizer)
    result = vqe.compute_minimum_eigenvalue(H_acoustic)
    
    E_min = result.eigenvalue.real
    
    # The minimum energy E_min is the Acoustic Dissonance Score
    # VQE returns a minimum *eigenvalue*, so E_min can be negative. We take its magnitude.
    return abs(E_min)

def calculate_acoustic_coherence_factor(E_min: float, f_ref: float) -> float:
    """
    Calculates the Acoustic Coherence Factor (F_AC) using the VQE result E_min.
    """
    # F_AC = alpha_AC * ( 1 - E_min(A) / E_max ) * cos( 2*pi*f_ref / f_Schumann )
    
    # 1. Normalize E_min
    normalized_dissonance = min(E_min, E_MAX) / E_MAX
    
    # 2. Coherence Term (1 - Normalized Dissonance)
    coherence_term = 1.0 - normalized_dissonance
    
    # 3. Schumann Resonance Term
    schumann_term = np.cos(2.0 * np.pi * f_ref / F_SCHUMANN)
    
    # 4. Final F_AC
    F_AC = ALPHA_AC * coherence_term * schumann_term
    
    return F_AC

# --- Example Application: Coherent vs. Dissonant Tone ---
if __name__ == "__main__":
    # Spectrum: Assuming 8 spectral components (relative intensities) around 432 Hz
    
    # A. Coherent Spectrum (432 Hz base, Phi-harmonic structure is strong)
    # Example: A pure 432 Hz (q0=1.0) and a strong 2nd harmonic (q4=0.8)
    # The indices represent the 8 spectral modes (e.g., q0 is the fundamental, q4 is the 2nd harmonic)
    spectrum_coherent = [1.0, 0.05, 0.2, 0.0, 0.8, 0.0, 0.0, 0.0] 
    f_ref_coherent = 432.0
    
    print("--- 1. Coherent Tone (432 Hz, Phi-Harmonic) ---")
    H_coherent = create_acoustic_hamiltonian(spectrum_coherent)
    E_min_coherent = run_qak_vqe(H_coherent)
    F_AC_coherent = calculate_acoustic_coherence_factor(E_min_coherent, f_ref_coherent)
    
    print(f"   Acoustic Dissonance Score (E_min): {E_min_coherent:.4f}")
    print(f"   Acoustic Coherence Factor (F_AC): {F_AC_coherent:.4f} (Should be HIGH)")

    # B. Dissonant Spectrum (440 Hz base, non-harmonic structure)
    # Example: A pure tone with a complex, non-harmonic distortion profile.
    spectrum_dissonant = [0.9, 0.5, 0.1, 0.0, 0.2, 0.3, 0.0, 0.1]
    f_ref_dissonant = 440.0
    
    print("\n--- 2. Dissonant Tone (440 Hz, Non-Phi-Harmonic) ---")
    H_dissonant = create_acoustic_hamiltonian(spectrum_dissonant)
    E_min_dissonant = run_qak_vqe(H_dissonant)
    F_AC_dissonant = calculate_acoustic_coherence_factor(E_min_dissonant, f_ref_dissonant)
    
    print(f"   Acoustic Dissonance Score (E_min): {E_min_dissonant:.4f}")
    print(f"   Acoustic Coherence Factor (F_AC): {F_AC_dissonant:.4f} (Should be LOW)")
    
    # Conclusion: The difference in F_AC (F_AC_coherent - F_AC_dissonant) is the predicted signal for the L-FED experiment.
    print("\n--- AEQET Prediction ---")
    print(f"Differential F_AC for L-FED: {F_AC_coherent - F_AC_dissonant:.4f}")
