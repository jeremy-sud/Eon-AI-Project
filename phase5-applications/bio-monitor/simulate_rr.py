import random
import sys

def generate_rr_stream(n_samples=500):
    """
    Generates synthetic RR intervals (Heart Rate Variability).
    Normal: ~60-100 BPM (1000ms - 600ms RR).
    Anomaly: Sudden drop (PVC) or spike (Missed beat).
    """
    
    # Base heart rate (60 BPM = 1000ms)
    rr = 1000.0
    
    # Respiratory Sinus Arrhythmia (RSA) simulation
    # Simple sine modulation
    import math
    
    for t in range(n_samples):
        # Normal Variation (RSA + Noise)
        rsa = 50.0 * math.sin(t * 0.2)
        noise = random.gauss(0, 10)
        
        current_rr = rr + rsa + noise
        
        # Inject Anomaly (Premature Ventricular Contraction)
        # every ~100 beats
        if t > 50 and t % 100 == 0:
            current_rr = current_rr * 0.6 # Early beat (short RR)
            sys.stderr.write(f"ANOMALY at t={t}: {current_rr:.2f}\n")
        
        # Compensatory Pause after PVC
        elif t > 51 and (t-1) % 100 == 0:
            current_rr = current_rr * 1.4 # Long pause
            
        print(f"{current_rr:.2f}")

if __name__ == "__main__":
    generate_rr_stream()
