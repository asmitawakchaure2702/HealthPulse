import subprocess
import sys
import os
from threading import Thread
import webbrowser
import time

def run_backend():
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    os.chdir(backend_dir)
    subprocess.run([sys.executable, 'app.py'])

def run_frontend():
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    os.chdir(frontend_dir)
    subprocess.run([sys.executable, '-m', 'http.server', '8000'])

def open_browser():
    time.sleep(2)  # Wait for servers to start
    webbrowser.open('http://localhost:8000')
    webbrowser.open('http://localhost:5000')

if __name__ == '__main__':
    # Start backend server in a separate thread
    backend_thread = Thread(target=run_backend)
    backend_thread.daemon = True
    backend_thread.start()

    # Start frontend server in a separate thread
    frontend_thread = Thread(target=run_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()

    # Open browser tabs
    browser_thread = Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()

    try:
        # Keep the main thread running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...") 