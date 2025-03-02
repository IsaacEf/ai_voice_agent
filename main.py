import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import requests
import os
from dotenv import load_dotenv

load_dotenv()  
API_KEY = os.getenv("BLAND_API_KEY")
if not API_KEY:
    raise ValueError("No API key set for BLAND_API_KEY environment variable")

HEADERS = {'Authorization': f'Bearer {API_KEY}'}

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

def call_conversational_endpoint(transcribed_text):
    #Sends the transcribed text to Bland AI's conversation endpoint and returns the response.
    
    url = "https://api.bland.ai/v1/calls" 
    # Construct the payload as required by the API
    payload = {
        "message": transcribed_text,
        "phone_number": '3477-979-555',       # Required parameter
        "task": "Your name is Brandon and you are calling me about getting on Marvel Rivals but you need to force me to play because you suck",   # Required parameter
        "objective": "conversation"  
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 200:
        data = response.json()
        # Adjust key names as per actual response structure
        ai_response = data.get('response', '')
        return ai_response
    else:
        print("Error calling conversational endpoint:", response.text)
        return ""

def main():
    # Record audio for 5 seconds
    recording, fs = record_audio(duration=5)
    
    # Save the recorded audio to a file
    output_filename = "test_recording.wav"
    sf.write(output_filename, recording, fs)
    print(f"Audio has been saved to {output_filename}")
    
    # Transcribe the recorded audio
    transcription = transcribe_audio(output_filename)
    
    # Send transcription to the AI's conversational endpoint
    if transcription:
        ai_response = call_conversational_endpoint(transcription)
        print("AI Response:", ai_response)
    else:
        print("No transcription available, skipping API call.")

if __name__ == "__main__":
    main()
