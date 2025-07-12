import threading
import webbrowser
import time
import os
import subprocess
import socket
import sys

from flask import Flask, render_template, redirect, url_for, flash
from PIL import Image, ImageDraw
import pystray

# -------------------- Flask App Setup --------------------

app = Flask(__name__)
app.secret_key = 'your_secret_key'

EXE_NAME = "ShairportQt.exe"
EXE_PATH = r"C:\Users\johns\AppData\Local\Programs\bin\ShairportQt.exe"
HTTP_PORT = 5000

# -------------------- Singleton Instance Lock --------------------

def is_already_running(port=HTTP_PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        result = sock.connect_ex(('127.0.0.1', port))
        return result == 0

# -------------------- Process Control --------------------

def is_process_running(exe_name):
    try:
        output = subprocess.check_output(["tasklist"], text=True)
        return exe_name.lower() in output.lower()
    except subprocess.CalledProcessError:
        return False

def stop_process_by_name(exe_name):
    try:
        subprocess.run(["taskkill", "/f", "/im", exe_name], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def start_process(path):
    try:
        subprocess.Popen(["start", "", path], shell=True)
    except Exception as e:
        print(f"Failed to start process: {e}")

def restart_target_process():
    if not os.path.isfile(EXE_PATH):
        print("Executable path is invalid or not found.")
        return False
    if is_process_running(EXE_NAME):
        stop_process_by_name(EXE_NAME)
        time.sleep(1)
    start_process(EXE_PATH)
    return True

# -------------------- Flask Routes --------------------

@app.route('/')
def index():
    return render_template('index.html', exe_name=EXE_NAME)

@app.route('/restart', methods=['POST'])
def restart_route():
    success = restart_target_process()
    if success:
        flash("Process restarted successfully!", "success")
    else:
        flash("Failed to restart process.", "error")
    return redirect(url_for('index'))

# -------------------- HTTP Server --------------------

def run_flask():
    app.run(host='0.0.0.0', port=HTTP_PORT, debug=False)

# -------------------- System Tray Integration --------------------

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def create_image():
    image = Image.new('RGB', (64, 64), 'white')
    draw = ImageDraw.Draw(image)
    draw.rectangle((16, 16, 48, 48), fill='blue')
    draw.text((12, 22), "Air", fill='white')
    return image

def on_open_ui(icon, item):
    ip = get_local_ip()
    webbrowser.open(f"http://{ip}:{HTTP_PORT}")

def on_restart(icon, item):
    restart_target_process()

def on_exit(icon, item):
    icon.stop()
    os._exit(0)

def run_tray_icon():
    icon = pystray.Icon("ShairportController")
    icon.icon = create_image()
    icon.title = "ShairportQt Restarter"
    icon.menu = pystray.Menu(
        pystray.MenuItem("Open Web UI", on_open_ui),
        pystray.MenuItem("Restart ShairportQt", on_restart),
        pystray.MenuItem("Exit", on_exit)
    )
    icon.run()

# -------------------- Main Entry --------------------

if __name__ == "__main__":
    if is_already_running():
        print("An instance is already running. Exiting.")
        sys.exit(0)

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    run_tray_icon()
