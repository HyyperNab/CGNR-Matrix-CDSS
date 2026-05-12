import numpy as np

# === CRP SIGMOID ATTENUATION MODEL ===
# Gate 1: Dynamic Floor — resolves SPOF P0‑1 (Sepsis Overestimation)
# Reference: Main Paper Eq. 3; CDSS Manual §2.2

def h_hormonal_attenuation(crp_value, k=0.1, crp_inflection=50.0):
    """
    Compute hormonal attenuation coefficient.
    
    Parameters:
        crp_value (float): Serum CRP in mg/dL.
        k (float): Sigmoid steepness.
            Theoretical baseline; clinical calibration reserved for future work.
        crp_inflection (float): CRP threshold for sepsis (mg/dL).
            Reference: McClave 2016 [12], Singer 2019 [13].
    
    Returns:
        tuple: (h_value, gate_status)
            h_value = 0.0 if Hard Stop, else sigmoid output.
            gate_status = "HARD_STOP" if CRP > 50, else "PASS".
    """
    if crp_value > crp_inflection:
        return 0.0, "HARD_STOP"
    else:
        h_val = 1.0 / (1.0 + np.exp(k * (crp_value - crp_inflection)))
        return h_val, "PASS"


# === VISUALISATION (optional) ===
def plot_attenuation_curve():
    import matplotlib.pyplot as plt
    
    crp_range = np.linspace(0, 100, 200)
    h_values = []
    
    for crp in crp_range:
        h, _ = h_hormonal_attenuation(crp)
        h_values.append(h)
    
    plt.figure(figsize=(10, 5))
    plt.plot(crp_range, h_values, 'b-', linewidth=2, label='h_hormonal')
    plt.axvline(x=50, color='red', linestyle='--', alpha=0.7, label='CRP = 50 (Hard Stop)')
    plt.fill_between(crp_range, 0, 1, where=(crp_range > 50), 
                     color='red', alpha=0.1, label='Hard Stop Zone')
    plt.xlabel('Serum CRP (mg/dL)')
    plt.ylabel('h_hormonal')
    plt.title('Gate 1: CRP‑Dependent Hormonal Attenuation')
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig('crp_sigmoid_gate1.png', dpi=150)
    plt.show()


if __name__ == "__main__":
    test_crp = [10, 30, 45, 50, 55, 80]
    for crp in test_crp:
        h, status = h_hormonal_attenuation(crp)
        print(f"CRP={crp:3d} mg/dL → h={h:.4f} [{status}]")
