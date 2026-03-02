import subprocess
import time
import os
import sys

def start_services():
    print("🚀 Starting SHL Recommender System on Hugging Face...")
    
    # 1. Start the FastAPI Backend in the background
    # Set the port to 8000 internally
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    print("⌛ Waiting for API to stabilize...")
    time.sleep(5)
    
    # Check if API started successfully
    if api_process.poll() is not None:
        print("❌ Backend failed to start. Logs:")
        print(api_process.stdout.read())
        return

    print("✅ Backend is LIVE on port 8000.")

    # 2. Start the Streamlit Frontend
    # Hugging Face Spaces expects the app on port 7860
    port = os.environ.get("PORT", "7860")
    print(f"📡 Launching Streamlit UI on port {port}...")
    
    # Note: frontend/app.py is already configured to look at localhost:8000 if no API_URL is set
    streamlit_process = subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "frontend/app.py", 
         "--server.port", port, "--server.address", "0.0.0.0"]
    )

if __name__ == "__main__":
    start_services()
