from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO
import threading
import time
import os

class CASEUI:
    def __init__(self, root_dir):
        self.app = Flask(__name__, template_folder=os.path.join(root_dir, 'web'), static_folder=os.path.join(root_dir, 'web', 'static'))
        # Using async_mode='threading' to avoid eventlet/gevent conflicts with sounddevice on Windows
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        self.root_dir = root_dir

        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            return send_from_directory(self.app.static_folder, filename)

    def write_log(self, text):
        print(f"LOG: {text}")
        self.socketio.emit('new_log', {'text': text})

    def update_transcript(self, text):
        self.socketio.emit('transcript', {'text': text})

    def start_speaking(self):
        self.socketio.emit('speaking_status', {'speaking': True})

    def stop_speaking(self):
        self.socketio.emit('speaking_status', {'speaking': False})

    def update_emotion(self, emotion, confidence=0.9):
        self.socketio.emit('emotion_update', {'emotion': emotion, 'confidence': confidence})

    def run(self, host='0.0.0.0', port=5000):
        print(f"🚀 CAS-E Web UI running at http://{host}:{port}")
        # When using threading mode, we don't need additional wrappers
        self.socketio.run(self.app, host=host, port=port, log_output=False, allow_unsafe_werkzeug=True)

def start_web_interface(ui_instance):
    ui_instance.run()

if __name__ == '__main__':
    ui = CASEUI(os.getcwd())
    threading.Thread(target=start_web_interface, args=(ui,), daemon=True).start()
    while True:
        time.sleep(1)
