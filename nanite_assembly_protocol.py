import numpy as np
import math
from typing import Union

# --- ESQET Constants and Parameters ---
# Green Motif Frequency (540 THz)
F_GM: float = 5.40e14  # Hz
# Standard Deviation of the Resonance (Set empirically for a tight resonance)
SIGMA_GM: float = 1.5e12  # Hz (0.0015 THz)
# Amplitude of the Gratitude Field (A_G), acts as max gain
A_G: float = 1.0  # Max gain factor

def calculate_gratitude_resonance_factor(f_local: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    r"""
    Calculates the Gratitude Resonance Factor (G_res) based on the local energy/information field frequency (f_local).

    The function uses a Gaussian distribution centered on the Green Motif frequency (F_GM).
    G_res = A_G * exp( - (f_local - F_GM)^2 / (2 * SIGMA_GM^2) )

    Args:
        f_local: The local frequency of the energy/information field in Hertz (Hz).

    Returns:
        The Gratitude Resonance Factor (G_res), a dimensionless scalar between 0 and A_G.
    """
    if not isinstance(f_local, (float, np.ndarray)):
        raise TypeError("Input frequency must be a float or numpy array.")

    # Calculate the exponent term
    exponent = - (f_local - F_GM)**2 / (2 * SIGMA_GM**2)

    # Calculate the G_res factor
    g_res = A_G * np.exp(exponent)

    return g_res

def modulate_coherence_for_nanites(F_QC: float, D_ent: float, f_local: float, D_min: float = 1e-12) -> float:
    r"""
    Applies the G-Field modulation to the Quantum Coherence Function (F_QC) to get F_QC'.

    F_QC' = F_QC * ( 1 + G_res * (D_ent / D_min) )

    Args:
        F_QC: The baseline Quantum Coherence Function value.
        D_ent: The local Entanglement Density.
        f_local: The local frequency (to calculate G_res).
        D_min: The minimum required entanglement density for G-Field activation.

    Returns:
        The modulated (G-enhanced) Quantum Coherence Function value (F_QC').
    """
    G_res = calculate_gratitude_resonance_factor(f_local)

    # Ensure D_ent / D_min ratio is calculated safely (prevent division by zero)
    if D_min <= 0:
        D_min = 1e-15 # Safety floor
        
    modulation_term = G_res * (D_ent / D_min)
    
    F_QC_prime = F_QC * (1.0 + modulation_term)
    
    return F_QC_prime

# --- Example Usage for Omni-Nanite Assembly ---
if __name__ == "__main__":
    # --- Test 1: Perfect Green Motif Resonance ---
    perfect_freq = F_GM
    g_res_perfect = calculate_gratitude_resonance_factor(perfect_freq)
    print(f"Test 1: Local Frequency: {perfect_freq:.2e} Hz")
    print(f"       G_res (Perfect Resonance): {g_res_perfect:.4f}") # Should be very close to A_G (1.0)
    
    # --- Test 2: Off-Resonance (e.g., Red Light) ---
    red_light_freq = 4.50e14  # Hz
    g_res_red = calculate_gratitude_resonance_factor(red_light_freq)
    print(f"\nTest 2: Local Frequency: {red_light_freq:.2e} Hz (Red)")
    print(f"       G_res (Off-Resonance): {g_res_red:.4e}") # Should be near zero
    
    # --- Test 3: Nanite Assembly Rate Simulation ---
    baseline_coherence = 0.5   # F_QC (baseline coherence)
    entanglement_density = 5e-12 # D_ent (high entanglement)
    min_density = 1e-12        # D_min

    # Assembly 1: Perfect Resonance (Max Gain)
    F_QC_prime_perfect = modulate_coherence_for_nanites(
        baseline_coherence, entanglement_density, perfect_freq, min_density
    )
    # The rate should be highly amplified: 0.5 * (1 + 1.0 * (5e-12/1e-12)) = 3.0
    print(f"\nTest 3: Nanite Assembly Simulation (Perfect Resonance):")
    print(f"       Modulated Coherence (F_QC'): {F_QC_prime_perfect:.4f} (6x baseline)")

    # Assembly 2: Off Resonance (Low Gain)
    F_QC_prime_red = modulate_coherence_for_nanites(
        baseline_coherence, entanglement_density, red_light_freq, min_density
    )
    # The rate should be barely amplified: 0.5 * (1 + ~0 * 5) ≈ 0.5
    print(f"       Modulated Coherence (F_QC') (Red Light): {F_QC_prime_red:.4f} (Near baseline)")
    
    print("\nConclusion: Omni-Nanite assembly is effectively shut down without the Green Motif resonance.")

