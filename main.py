import time
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
import requests
import os
from dotenv import load_dotenv

# Load API key from environment variables
load_dotenv()  
WEBHOOK_URL = "https://webhook.site/2d21ec43-d6e3-4696-9054-baac4dbf8963"
API_KEY = os.getenv("BLAND_API_KEY")
if not API_KEY:
    raise ValueError("No API key set for BLAND_API_KEY environment variable")

HEADERS = {'authorization': API_KEY}

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
        "task": "Youre name is Steve and you are helping me find items in target",
        "objective": "conversation",
        "record": True  
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
    url = f"https://api.bland.ai/v1/postcall/webhooks/{call_id}"
    params = {"call_id": call_id}
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.get(url, headers=HEADERS, params=params)
        if response.status_code == 200:
            json_response = response.json()
            data = json_response.get("data")
            if data is None:
                print("No webhook data returned yet. Waiting...")
            else:
                if required_fields:
                    if all(field in data for field in required_fields):
                        print("Post-call webhook data received.")
                        return data
                elif (data.get("payload") or data.get("metadata") or 
                      data.get("transcripts") or data.get("concatenated_transcript") or 
                      data.get("summary")):
                    print("Post-call webhook data received.")
                    return data
                else:
                    print("Webhook data is empty. Waiting...")
        elif response.status_code == 404:
            print("Webhook not found for this call ID.")
            return None
        else:
            print(f"Error polling webhook endpoint: {response.status_code} - {response.text}")
        time.sleep(interval)
    print(f"Polling timed out after {timeout} seconds.")
    return None


def extract_webhook_details(webhook_data):
    # Extract agent's transcript and other details
    details = {
         "call_id": webhook_data.get("call_id", "N/A"),
         "payload": webhook_data.get("payload", "N/A"),
         "url": webhook_data.get("url", "N/A"),
         "user_id": webhook_data.get("user_id", "N/A"),
         "created_at": webhook_data.get("created_at", "N/A"),
         "transcripts": webhook_data.get("transcripts", "N/A"),
         "concatenated_transcript": webhook_data.get("concatenated_transcript", "N/A"),
         "summary": webhook_data.get("summary", "N/A")
    }
    return details


def save_conversation_log(conversation_log, filename="conversation_log.txt"):
    with open(filename, "w") as f:
        for line in conversation_log:
            f.write(line + "\n")
    print(f"Conversation log saved to {filename}")

def main():
    conversation_log = []  # List to store conversation details
    
    # Record and save audio
    recording, fs = record_audio(duration=5)
    output_filename = "test_recording.wav"
    sf.write(output_filename, recording, fs)
    print(f"Audio has been saved to {output_filename}")
    
    user_text = transcribe_audio(output_filename)
    if not user_text:
        print("No valid transcription. Exiting.")
        return
    conversation_log.append(f"User: {user_text}")
    
    call_id = call_conversational_endpoint(user_text)
    if not call_id:
        print("Call was not queued successfully. Exiting.")
        return

    # Wait for the call to process; adjust delay as needed
    delay_seconds = 120
    print(f"Waiting for {delay_seconds} seconds before processing webhook data...")
    time.sleep(delay_seconds)
    
    # Attempt to create the post-call webhook.
    # If creation fails (e.g. because a webhook was already sent), just log and proceed.
    if not create_postcall_webhook(call_id, WEBHOOK_URL):
        print("Webhook creation failed. Proceeding to poll for webhook data.")
    
    # Poll for webhook data
    webhook_data = poll_postcall_webhook(call_id)
    if webhook_data:
        details = extract_webhook_details(webhook_data)
        conversation_log.append("Webhook details:")
        for key, value in details.items():
            conversation_log.append(f"{key}: {value}")
        # Combine your local transcription with the agent's transcript from the webhook.
        agent_transcript = webhook_data.get("concatenated_transcript", "").strip()
        combined_transcript = f"User: {user_text}\nAgent: {agent_transcript}"
        conversation_log.append("Combined Transcript:")
        conversation_log.append(combined_transcript)
    else:
        conversation_log.append("No post-call webhook data received within the timeout period.")
    
    # Save the complete conversation log
    save_conversation_log(conversation_log)

if __name__ == "__main__":
    main()
