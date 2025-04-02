import librosa
import numpy as np
import pygame
import time
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

# Initialize pygame mixer
pygame.mixer.init()

# Load the MP3 file
mp3_file = "../audio/heartbeat.mp3"
y, sr = librosa.load(mp3_file, sr=None)  # Preserve original sample rate

# Take the absolute value of the audio signal
y_abs = np.abs(y)

# Smooth the signal using a Gaussian filter to reduce noise
smoothed_signal = gaussian_filter1d(y_abs, sigma=5)  # Adjust sigma for smoothing level

# Find local maxima (peaks) in the smoothed signal
peaks, _ = find_peaks(smoothed_signal, height=0.5, distance=sr//10)  # Adjust the distance for peak separation

# Convert peak indices to times
peak_times = librosa.samples_to_time(peaks, sr=sr)

# Trigger S1 based on peaks and detect S2 within 400ms
s1_times = []
s2_times = []

# Introduce a cooldown time of 500ms after detecting an S2 to avoid new S1 detection too soon
cooldown_time = 0.5  # in seconds
last_s2_time = -cooldown_time  # Initial cooldown time set to allow first S1

for s1_time in peak_times:
    # Skip S1 if it occurs too soon after an S2 (within cooldown period)
    if s1_time <= last_s2_time + cooldown_time:
        continue

    s1_times.append(s1_time)
    # Find S2 within 400ms of S1
    s2_time_candidates = peak_times[peak_times > s1_time]  # Candidates after S1
    s2_time_candidates = s2_time_candidates[s2_time_candidates <= s1_time + 0.4]  # Within 400ms
    
    if len(s2_time_candidates) > 0:
        s2_times.append(s2_time_candidates[0])  # First S2 after S1
        last_s2_time = s2_time_candidates[0]  # Update last S2 time to prevent S1 detection too soon
    else:
        s2_times.append(None)

# Initialize audio playback
pygame.mixer.music.load(mp3_file)
pygame.mixer.music.play()

# Wait for the audio to start
time.sleep(1)  # Adjust if necessary for audio delay

# Print detected S1 and S2 times with audio synchronization
for i, s1 in enumerate(s1_times):
    # Wait for the time corresponding to S1
    while pygame.mixer.music.get_pos() / 1000.0 < s1:  # Convert milliseconds to seconds
        time.sleep(0.01)  # Small delay to avoid busy-waiting

    print(f"S1 detected at {s1:.3f}s")

    if s2_times[i]:
        while pygame.mixer.music.get_pos() / 1000.0 < s2_times[i]:
            time.sleep(0.01)

        print(f"S2 detected at {s2_times[i]:.3f}s")
    else:
        print("No S2 detected within 400ms")

# Wait for the audio to finish playing
while pygame.mixer.music.get_busy():
    time.sleep(0.1)  # Small delay to prevent maxing out CPU usage

