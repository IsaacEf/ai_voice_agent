from flask import Flask, request
import threading

app = Flask(__name__)
webhook_payload = None

@app.route('/webhook', methods=['POST'])
def webhook():
    global webhook_payload
    webhook_payload = request.json
    print("Webhook received:", webhook_payload)
    return '', 200

def run_server():
    app.run(port=5000)

# Start the Flask server in a separate thread
server_thread = threading.Thread(target=run_server)
server_thread.daemon = True
server_thread.start()
