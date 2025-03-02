import sounddevice as sd
import soundfile as sf

def record_audio(duration=5, fs=16000):
    """
    Records audio from the default microphone.
    
    :param duration: Duration of recording in seconds.
    :param fs: Sampling frequency in Hz.
    :return: Tuple (audio data as a NumPy array, sampling frequency)
    """
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    print("Recording complete!")
    return recording, fs

def main():
    # Record audio for 5 seconds
    recording, fs = record_audio(duration=5)
    
    # Save the recorded audio to a file for verification
    output_filename = "test_recording.wav"
    sf.write(output_filename, recording, fs)
    print(f"Audio has been saved to {output_filename}")

if __name__ == "__main__":
    main()
