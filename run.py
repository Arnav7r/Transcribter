import os
import sys
import webbrowser
import threading
import time
import uvicorn

def open_browser():
    time.sleep(1.5)
    print("\n[+] Opening browser at http://localhost:8000 ...")
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    import app.config  # Initializes and registers FFmpeg in PATH
    print("=" * 65)
    print("   InstaTranscribe Hindi - Reels Audio to Written Hindi")
    print("=" * 65)
    print("[+] Starting web application server at: http://localhost:8000")
    print("[+] Press Ctrl+C in this terminal to stop the server.\n")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=False)

