#!/usr/bin/env python3
"""
ESQET-UIFT v3.2.4: FCU Resonance in GHZ Fidelity Scaling
Generates ghz_fcu_prediction.png for the whitepaper.
"""

import numpy as np
import matplotlib.pyplot as plt

# Golden ratio
phi = (1 + np.sqrt(5)) / 2

# Qubit range
N = np.arange(3, 14)

# Decay parameters
alpha = 0.08
beta = 0.025

# Standard exponential decay
F_standard = np.exp(-alpha * N)

# ESQET prediction with FCU modulation
F_esqet = F_standard * (1 + beta * np.cos(2 * np.pi * N / phi))

# Create plot
plt.figure(figsize=(8, 5.5), dpi=300)
plt.plot(N, F_standard, 'k--', label='Standard Decay', linewidth=2.2, alpha=0.9)
plt.plot(N, F_esqet, 'r-', label='ESQET: FCU-Modulated', linewidth=2.8)

# Highlight FCU nodes
fcu_nodes = [5, 8]
for n in fcu_nodes:
    idx = n - 3
    plt.scatter(n, F_esqet[idx], color='gold', s=140, zorder=6, edgecolors='black', linewidth=1.2)
    plt.axvline(n, color='gray', linestyle=':', alpha=0.6, linewidth=1.5)

plt.xlabel('Number of Qubits $N$', fontsize=13)
plt.ylabel('Fidelity $F(N)$', fontsize=13)
plt.title('ESQET Prediction: FCU Resonance in GHZ Fidelity Scaling', fontsize=14, pad=15)
plt.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
plt.grid(True, alpha=0.3, linestyle='-', linewidth=0.8)
plt.ylim(0, 1.05)
plt.xlim(2.8, 13.2)
plt.tight_layout()

# Save
plt.savefig('../ghz_fcu_prediction.png', dpi=300, bbox_inches='tight', facecolor='white')
print("ghz_fcu_prediction.png generated successfully!")
plt.close()
