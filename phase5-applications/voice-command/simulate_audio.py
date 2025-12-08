import random
import sys

def generate_audio_stream(n_frames=1000):
    """
    Simulates 4-band filterbank output (50Hz sample rate).
    Bands: [Low, Mid1, Mid2, High]
    Keyword "EON":
      - 'E' (Mid-High energy) for 5 frames
      - 'O' (Low-Mid energy) for 5 frames
      - 'N' (Low energy + Nasal) for 5 frames
    Length: ~15-20 frames (300-400ms)
    """
    
    # 0 = Silence/Background Noise
    # 1 = Keyword Target active
    
    stream = []
    labels = []
    
    t = 0
    while t < n_frames:
        # P(Keyword) = 0.05 per frame if waiting
        if random.random() < 0.02:
            # Inject "EON"
            # 1. 'E' (High Mids)
            for _ in range(5):
                stream.append([0.1, 0.2, 0.8, 0.4]) # Band 3 dominant
                labels.append(0)
                t += 1
            # 2. 'O' (Low Mids)
            for _ in range(5):
                stream.append([0.2, 0.9, 0.3, 0.1]) # Band 2 dominant
                labels.append(0)
                t += 1
            # 3. 'N' (Low)
            for _ in range(5):
                stream.append([0.8, 0.3, 0.1, 0.0]) # Band 1 dominant
                labels.append(1) # Target fires at end of word
                t += 1
            
            # Post-word silence
            for _ in range(3):
                stream.append([0.05, 0.05, 0.05, 0.05])
                labels.append(0)
                t += 1
        else:
            # Background Noise (random fluctuation)
            noise_profile = [random.random()*0.2 for _ in range(4)]
            # Occasional random burst (false positive bait)
            if random.random() < 0.1:
                noise_profile[random.randint(0,3)] += 0.5
                
            stream.append(noise_profile)
            labels.append(0)
            t += 1
            
    # Output CSV-ish format: B1,B2,B3,B4,TARGET
    print("B1,B2,B3,B4,TARGET")
    for s, l in zip(stream, labels):
        # Add some gaussian noise to bands
        s_noisy = [max(0.0, min(1.0, v + random.gauss(0, 0.05))) for v in s]
        line = f"{s_noisy[0]:.2f},{s_noisy[1]:.2f},{s_noisy[2]:.2f},{s_noisy[3]:.2f},{l}"
        print(line)

if __name__ == "__main__":
    generate_audio_stream(2000)
