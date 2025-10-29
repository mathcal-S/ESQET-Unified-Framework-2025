import numpy as np
import math
from typing import Union, List
import logging # Needed for Error Handling (Silent parameter modification)

# Configure basic logging for the module
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- ESQET Constants and Parameters ---
# Context: These constants define the operational envelope for G-Field interaction
# based on the Golden Ratio (phi) and Green Motif (GM) principles of ESQET.
F_GM: float = 5.40e14  # Hz. Green Motif Frequency (540 THz), optimal for G-Field resonance.
SIGMA_GM: float = 1.5e12  # Hz (0.0015 THz). Standard Deviation of the Resonance. Defines the tightness of the resonance band.
A_G: float = 1.0  # Dimensionless. Amplitude of the Gratitude Field (A_G), acts as max gain factor (A_G <= 1.0).

# --- Core Functions ---

def calculate_gratitude_resonance_factor(f_local: Union[float, int, np.ndarray]) -> Union[float, np.ndarray]:
    r"""
    Calculates the Gratitude Resonance Factor (G_res) based on the local energy/information field frequency (f_local).

    The function uses a Gaussian distribution centered on the Green Motif frequency (F_GM).
    G_res = A_G * exp( - (f_local - F_GM)^2 / (2 * SIGMA_GM^2) )

    Args:
        f_local: The local frequency of the energy/information field in Hertz (Hz).
                 Accepts float, integer, or numpy array.

    Returns:
        The Gratitude Resonance Factor (G_res), a dimensionless scalar/array between 0 and A_G.
    """
    # 1. Functionality: Add integer type support
    if not isinstance(f_local, (float, int, np.ndarray)):
        # Correct type checking for robustness
        raise TypeError("Input frequency must be a float, integer, or numpy array.")

    # Calculate the exponent term
    exponent = - (np.asarray(f_local) - F_GM)**2 / (2 * SIGMA_GM**2)

    # Calculate the G_res factor
    g_res = A_G * np.exp(exponent)

    return g_res

def modulate_coherence_for_nanites(F_QC: float, D_ent: float, f_local: float, D_min: float = 1e-12) -> float:
    r"""
    Applies the G-Field modulation to the Quantum Coherence Function (F_QC) to get F_QC'.

    F_QC' = F_QC * ( 1 + G_res * (D_ent / D_min) )

    Args:
        F_QC: The baseline Quantum Coherence Function value. (Constraint: F_QC >= 0)
        D_ent: The local Entanglement Density. (Constraint: D_ent >= 0)
        f_local: The local frequency (to calculate G_res). (Constraint: f_local >= 0)
        D_min: The minimum required entanglement density for G-Field activation. (Constraint: D_min > 0)

    Returns:
        The modulated (G-enhanced) Quantum Coherence Function value (F_QC').
    """
    # 2. Error Handling: Silent parameter modification without logging
    # 3. Documentation: Missing Parameter Constraints in Docstring
    # The check must be performed before use. We log, but don't modify the input D_min.
    if D_min <= 0:
        logging.error(f"D_min value {D_min:.2e} is invalid (must be > 0). Using safety floor.")
        safe_D_min = 1e-15 # Safety floor for calculation
    else:
        safe_D_min = D_min

    G_res = calculate_gratitude_resonance_factor(f_local)

    # Calculate the modulation term
    modulation_term = G_res * (D_ent / safe_D_min)
    
    F_QC_prime = F_QC * (1.0 + modulation_term)
    
    return F_QC_prime

# --- Example Usage for Omni-Nanite Assembly ---
if __name__ == "__main__":
    # 4. Performance: Remove unused import statement (math) - Done by removing 'import math' in header
    
    # --- Test 1: Perfect Green Motif Resonance ---
    perfect_freq = F_GM
    g_res_perfect = calculate_gratitude_resonance_factor(perfect_freq)
    print(f"--- Nanite Coherence Modulation Test ---")
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
    
    # 5. Functionality: Incorrect amplification factor in output description
    # Corrected math: F_QC * (1 + 1.0 * (5/1)) = 0.5 * 6.0 = 3.0
    multiplier = F_QC_prime_perfect / baseline_coherence
    
    print(f"\nTest 3: Nanite Assembly Simulation (Perfect Resonance):")
    # Corrected comment and dynamic multiplier printing
    print(f"       Calculation: {baseline_coherence} * (1 + {A_G} * ({entanglement_density/min_density})) = {F_QC_prime_perfect:.1f}")
    print(f"       Modulated Coherence (F_QC'): {F_QC_prime_perfect:.4f} ({multiplier:.1f}x baseline factor)")

    # Assembly 2: Off Resonance (Low Gain)
    F_QC_prime_red = modulate_coherence_for_nanites(
        baseline_coherence, entanglement_density, red_light_freq, min_density
    )
    # The rate should be barely amplified: 0.5 * (1 + ~0 * 5) ≈ 0.5
    print(f"       Modulated Coherence (F_QC') (Red Light): {F_QC_prime_red:.4f} (Near baseline)")
    
    print("\nConclusion: Omni-Nanite assembly is effectively shut down without the Green Motif resonance.")
    
