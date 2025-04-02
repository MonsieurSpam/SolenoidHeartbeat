import librosa
import numpy as np
import pygame
import time
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

# Initialize pygame mixer with lower quality settings for better performance
pygame.mixer.init(frequency=11025, size=-16, channels=1)

# Function to analyze heartbeat once
def analyze_heartbeat(mp3_file):
    # Load the MP3 file with reduced resolution for Raspberry Pi 3B
    target_sr = 2000  # Low sample rate to reduce computation
    y, sr = librosa.load(mp3_file, sr=target_sr)  # Downsample during loading

    # Take the absolute value of the audio signal
    y_abs = np.abs(y)

    # Use Gaussian filter with reduced sigma for efficiency
    smoothed_signal = gaussian_filter1d(y_abs, sigma=2)

    # Find peaks with minimal parameters
    peaks, _ = find_peaks(smoothed_signal, height=0.4, distance=target_sr//5)

    # Convert peak indices to times
    peak_times = librosa.samples_to_time(peaks, sr=target_sr)

    # Trigger S1 based on peaks and detect S2 within 400ms
    s1_times = []
    s2_times = []

    # Introduce a cooldown time of 500ms after detecting an S2
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
            last_s2_time = s2_time_candidates[0]  # Update last S2 time
        else:
            s2_times.append(None)
    
    return s1_times, s2_times

# Function to play audio in a loop
def play_audio_loop(mp3_file):
    pygame.mixer.music.load(mp3_file)
    pygame.mixer.music.play(-1)  # -1 means loop indefinitely

# Function to display heartbeat events in sync with audio
def display_heartbeat_events(s1_times, s2_times, audio_length):
    start_time = time.time()
    cycle_count = 0
    
    # Track which events have been shown in current cycle
    s1_shown = set()
    s2_shown = set()
    
    try:
        while True:  # Run indefinitely until interrupted
            # Calculate current position in the audio loop
            elapsed = time.time() - start_time
            position_in_loop = elapsed % audio_length
            current_cycle = int(elapsed / audio_length)
            
            # Check if we've completed a cycle
            if current_cycle > cycle_count:
                cycle_count = current_cycle
                s1_shown.clear()  # Reset tracking for new cycle
                s2_shown.clear()
                print(f"\n--- Starting cycle {cycle_count} ---\n")
                
            # Find all S1 and S2 events that should occur at this position
            # Use a wider window (100ms) for checking but avoid showing duplicates
            for i, s1 in enumerate(s1_times):
                # Only show each S1 once per cycle with a tolerance window
                if i not in s1_shown and abs(position_in_loop - s1) < 0.1:
                    print(f"Cycle {cycle_count}: S1 detected at {s1:.3f}s")
                    s1_shown.add(i)
                    
                # Only show each S2 once per cycle
                if s2_times[i] and i not in s2_shown and abs(position_in_loop - s2_times[i]) < 0.1:
                    print(f"Cycle {cycle_count}: S2 detected at {s2_times[i]:.3f}s")
                    s2_shown.add(i)
            
            time.sleep(0.05)  # Larger delay to reduce checking frequency
            
    except KeyboardInterrupt:
        print("Monitoring stopped by user")

# Main function
def main():
    mp3_file = "../audio/heartbeat.mp3"
    
    # Analyze the heartbeat once
    print("Analyzing heartbeat pattern...")
    s1_times, s2_times = analyze_heartbeat(mp3_file)
    print(f"Analysis complete. Found {len(s1_times)} heartbeats.")
    
    # Get audio file length
    y, sr = librosa.load(mp3_file, sr=None)
    audio_length = librosa.get_duration(y=y, sr=sr)
    
    # Start the audio playback in a loop
    print("Starting audio playback...")
    play_audio_loop(mp3_file)
    
    # Display heartbeat events
    print("Monitoring heartbeats. Press Ctrl+C to stop.")
    display_heartbeat_events(s1_times, s2_times, audio_length)

if __name__ == "__main__":
    main()
