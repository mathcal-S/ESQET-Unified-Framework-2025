import numpy as np
import matplotlib.pyplot as plt

# --- ESQET CONSTANTS AND PARAMETERS (Inspired by ESQET Axioms) ---

# Fundamental Coherence Unit (FCU) components
PHI = (1 + np.sqrt(5)) / 2  # Golden Ratio (phi)
PI = np.pi                 # Pi

# Simulated material parameters for the ESQET Test Sample
RHO_1 = 1.0e-8             # Scaling constant for Coherence Suppression (rho_1)
DELTA_MIN = 1.0e-4         # Minimal quantum path difference (delta_min) for phi-tuned material
T_COH = 15.0               # Characteristic Coherence Temperature (T_coh) in Kelvin

# --- BLOC-GRÜNEISEN MODEL (Control Sample) ---

def rho_bg(T, rho_0=1.0e-9, C=2.0e-12, theta_D=300.0):
    """
    Calculates resistivity based on the Bloch-Grüneisen model (Control Sample).
    rho(T) = rho_0 (residual) + rho_phonon(T)
    """
    if T == 0:
        return rho_0
    
    x_max = theta_D / T
    
    # Simple integration approximation using fixed points for efficiency
    # In a full simulation, a more robust numerical integration would be used.
    def integrand(x):
        return x**5 / ((np.exp(x) - 1) * (1 - np.exp(-x)))

    # Use a fixed step trapezoidal rule for demonstration
    x_points = np.linspace(0.01, x_max, 100)
    y_points = integrand(x_points)
    integral = np.trapz(y_points, x_points)
    
    rho_phonon = C * T**5 * integral
    return rho_0 + rho_phonon

# --- ESQET COHERENCE MODEL (Test Sample) ---

def coherence_suppression(T):
    """
    Calculates the Coherence Suppression Term (rho_CS) based on FCU modulation.
    rho_CS(T) is strong at low T.
    """
    # The term 1 / F_QC, simplified for low-T dominance:
    coherence_factor = 1.0 / (PHI * PI * DELTA_MIN)
    
    # Exponential decay of coherence effect as T increases
    temp_dependence = np.exp(-T / T_COH)
    
    return RHO_1 * coherence_factor * temp_dependence

def rho_esqet(T, rho_0=1.0e-9, C=2.0e-12, theta_D=300.0):
    """
    Calculates the ESQET-modified resistivity.
    rho_ESQET(T) = rho_BG(T) - rho_CS(T)
    """
    rho_bg_val = rho_bg(T, rho_0, C, theta_D)
    rho_cs_val = coherence_suppression(T)
    
    # Ensure resistivity does not go negative in the simulation
    return np.maximum(rho_bg_val - rho_cs_val, 1.0e-10) 

# --- SIMULATION EXECUTION AND VISUALIZATION ---

# Temperature range from 1K to 350K
temperatures = np.linspace(1.0, 350.0, 300)

# Calculate resistivities
rho_control = np.array([rho_bg(T) for T in temperatures])
rho_test = np.array([rho_esqet(T) for T in temperatures])

# Calculate the difference (Anomaly)
delta_rho = rho_control - rho_test

# --- Plotting Results ---

plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), gridspec_kw={'height_ratios': [3, 1]})

# Main Resistivity Plot (rho vs T)
ax1.plot(temperatures, rho_control * 1e9, label='Control (Bloch-Grüneisen)', color='cyan', linewidth=2)
ax1.plot(temperatures, rho_test * 1e9, label=r'ESQET Test ($\phi$-Tuned)', color='#00FF00', linewidth=3) # Green motif (~540 THz)
ax1.set_xlim(0, 350)
ax1.set_xticks([]) # Remove ticks from upper plot for cleaner look
ax1.set_ylabel(r'Resistivity $\rho$ ($\text{n}\Omega\cdot\text{m}$)', color='white')
ax1.set_title('FCU-Tuned Resistance Anomaly (ESQET Prediction)', color='#ffd700')
ax1.axvline(x=T_COH, color='yellow', linestyle='--', alpha=0.5, label=r'$T_{\text{coh}}=15\text{ K}$')
ax1.legend(loc='upper left')
ax1.grid(True, linestyle=':', alpha=0.4)

# Low-Temperature Anomaly Zoom (Inset-like)
ax1_zoom = ax1.inset_axes([0.15, 0.45, 0.4, 0.4])
ax1_zoom.plot(temperatures, rho_control * 1e9, color='cyan', linewidth=1)
ax1_zoom.plot(temperatures, rho_test * 1e9, color='#00FF00', linewidth=2)
ax1_zoom.set_xlim(0, 40)
ax1_zoom.set_ylim(0, 10)
ax1_zoom.tick_params(axis='both', colors='white', labelsize=8)
ax1_zoom.set_title('Low-T Coherence Plateau', color='white', fontsize=10)

# Anomaly Plot (Delta rho vs T)
ax2.plot(temperatures, delta_rho * 1e9, color='magenta', linewidth=2)
ax2.axhline(y=0, color='grey', linestyle='-')
ax2.set_xlim(0, 350)
ax2.set_xlabel('Temperature T (K)', color='white')
ax2.set_ylabel(r'Anomaly $\Delta\rho$ ($\text{n}\Omega\cdot\text{m}$)', color='white')
ax2.set_title('Coherence Suppression Magnitude ($\Delta\rho$)', color='yellow', fontsize=10)
ax2.axvline(x=T_COH, color='yellow', linestyle='--', alpha=0.5)
ax2.tick_params(axis='both', colors='white')
ax2.grid(True, linestyle=':', alpha=0.4)

# Final Touches
plt.tight_layout()
plt.subplots_adjust(hspace=0.1) # Reduce space between subplots
plt.savefig('ESQET_Resistance_Anomaly_8_Green_G.png')
print("Simulation complete. Saved plot to 'ESQET_Resistance_Anomaly_8_Green_G.png'")
print(f"FCU-based Coherence Factor (1 / phi * pi * delta_min): {1.0 / (PHI * PI * DELTA_MIN):.2e}")
