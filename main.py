import time
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import requests
import os
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()  
API_KEY = os.getenv("BLAND_API_KEY")
if not API_KEY:
    raise ValueError("No API key set for BLAND_API_KEY environment variable")

HEADERS = {'Authorization': f'Bearer {API_KEY}'}

def record_audio(duration=5, fs=16000):
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()  # Wait until recording is finished
    print("Recording complete!")
    return recording, fs

def transcribe_audio(filename):
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
    url = "https://api.bland.ai/v1/calls"  
    payload = {
        "message": transcribed_text,
        "phone_number": "+19296003028",
        "task": "You are a store clerk at Target",
        "objective": "conversation"
    }
    print("Sending payload to trigger call:", payload)
    response = requests.post(url, headers=HEADERS, json=payload)
    print("Call endpoint status:", response.status_code)
    print("Call endpoint response:", response.text)
    
    if response.status_code == 200:
        data = response.json()
        call_id = data.get('call_id', '')
        if call_id:
            print("Call queued successfully with call_id:", call_id)
            return call_id
    else:
        print("Error details:", response.text)
    return None

def create_postcall_webhook(call_id, webhook_url):
    url = "https://api.bland.ai/v1/postcall/webhooks/create"

    payload = {
         "call_ids": [call_id],
         "webhook_url": webhook_url
    }
    print(f"Creating post-call webhook for call_id: {call_id}")
    response = requests.post(url, headers=HEADERS, json=payload)
    print(f"Webhook creation status: {response.status_code}")
    
    if response.status_code == 200:
        print("Webhook created successfully")
        return True
    else:
        print(f"Webhook creation failed: {response.text}")
        return False


def poll_postcall_webhook(call_id, timeout=300, interval=5, required_fields=None):
    # Endpoint to poll for webhook data
    url = f"https://api.bland.ai/v1/postcall/webhooks/{call_id}"
    params = {"call_id": call_id}
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            data = response.json()
            if required_fields:
                if all(field in data for field in required_fields):
                    print("Post-call webhook data received.")
                    return data
            elif data.get("payload") or data.get("metadata"):
                print("Post-call webhook data received.")
                return data
            else:
                print("No webhook data yet. Waiting...")
        elif response.status_code == 404:
            print("Webhook not found for this call ID.")
            return None
        else:
            print(f"Error polling webhook endpoint: {response.status_code} - {response.text}")
        time.sleep(interval)
    print(f"Polling timed out after {timeout} seconds.")
    return None

def extract_webhook_details(webhook_data):
    # Extract the desired fields from the webhook data, defaulting to "N/A" if not found.
    details = {
         "call_id": webhook_data.get("call_id", "N/A"),
         "payload": webhook_data.get("payload", "N/A"),
         "url": webhook_data.get("url", "N/A"),
         "user_id": webhook_data.get("user_id", "N/A"),
         "created_at": webhook_data.get("created_at", "N/A")
    }
    return details

def save_conversation_log(conversation_log, filename="conversation_log.txt"):
    with open(filename, "w") as f:
        for line in conversation_log:
            f.write(line + "\n")
    print(f"Conversation log saved to {filename}")

def main():
    conversation_log = []  # List to store conversation details
    
    # Record a single turn of audio
    recording, fs = record_audio(duration=5)
    output_filename = "test_recording.wav"
    sf.write(output_filename, recording, fs)
    print(f"Audio has been saved to {output_filename}")
    
    # Transcribe the recorded audio
    user_text = transcribe_audio(output_filename)
    if not user_text:
        print("No valid transcription. Exiting.")
        return
    conversation_log.append(f"User: {user_text}")
    
    # Queue the call using the user's transcription
    call_id = call_conversational_endpoint(user_text)
    if not call_id:
        print("Call was not queued successfully. Exiting.")
        return

    # Wait a few seconds before creating the webhook, allowing the call to process
    delay_seconds = 5
    print(f"Waiting for {delay_seconds} seconds before creating post-call webhook...")
    time.sleep(delay_seconds)
    
    # Set webhook URL 
    webhook_url = "https://webhook.site/2d21ec43-d6e3-4696-9054-baac4dbf8963"
    if not create_postcall_webhook(call_id, webhook_url):
        print("Failed to create post-call webhook. Continuing without explicit webhook creation.")
    
    # Poll until the call is complete and webhook data is available
    webhook_data = poll_postcall_webhook(call_id)
    if webhook_data:
        details = extract_webhook_details(webhook_data)
        conversation_log.append("Webhook details:")
        for key, value in details.items():
            conversation_log.append(f"{key}: {value}")
    else:
        conversation_log.append("No post-call webhook data received within the timeout period.")
    
    # Save the conversation log to a text file
    save_conversation_log(conversation_log)

if __name__ == "__main__":
    main()
