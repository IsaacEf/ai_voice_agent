import sounddevice as sd
import soundfile as sf
import speech_recognition as sr

def record_audio(duration=5, fs=16000):
    
    #Records audio from the default microphone.
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    print("Recording complete!")
    return recording, fs

def transcribe_audio(filename):
    #Transcribes the audio from a given WAV file using SpeechRecognition.
    
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
    try:
        transcription = recognizer.recognize_google(audio)
        print("Transcription:", transcription)
        return transcription
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand the audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    return ""

def main():
    # Record audio for 5 seconds
    recording, fs = record_audio(duration=5)
    
    # Save the recorded audio to a file for verification
    output_filename = "test_recording.wav"
    sf.write(output_filename, recording, fs)
    print(f"Audio has been saved to {output_filename}")
    
    # Transcribe the recorded audio
    transcribe_audio(output_filename)

if __name__ == "__main__":
    main()
