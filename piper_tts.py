import os
import requests
import tempfile
import subprocess
import threading
import queue
import select
import sys

# Global variable to track current audio process
current_audio_process = None
audio_lock = threading.Lock()

def speak_with_piper(text, server_url="http://localhost:5000"):
    global current_audio_process
    
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_wav = temp_file.name
        
        # Send POST request to Piper HTTP server
        payload = {'text': text}
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(server_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            # Save the audio data to temp file
            with open(temp_wav, 'wb') as f:
                for chunk in response.iter_content(chunk_size=4096):
                    f.write(chunk)
            
            # Play audio with process tracking
            with audio_lock:
                if os.name == 'posix':  # Linux/Mac
                    # Check if aplay exists (Linux), otherwise use afplay (Mac)
                    if os.system('which aplay > /dev/null 2>&1') == 0:
                        current_audio_process = subprocess.Popen(['aplay', temp_wav]) #Creates audio process object, that has certain features
                    else:
                        current_audio_process = subprocess.Popen(['afplay', temp_wav])
                else:  # Windows
                    current_audio_process = subprocess.Popen(['start', '/wait', temp_wav], shell=True)
            
            # Wait for audio to complete or be interrupted

            current_audio_process.wait() #Blocking process, ensures entire audio thread is played (except stop)
            
            with audio_lock:
                current_audio_process = None #Clears audio process for next audio 
            
            # Clean up temp file
            os.unlink(temp_wav)
            return #Stops Thread
            
        else:
            print(f"Error from Piper server: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Piper server. Make sure it's running on", server_url)
        return False
    except Exception as e:
        print(f"Error: {e}")
        # Clean up temp file if it exists
        if 'temp_wav' in locals() and os.path.exists(temp_wav):
            os.unlink(temp_wav)
        return False

def stop_audio():
    """Stop currently playing audio"""
    global current_audio_process
    
    with audio_lock:
        if current_audio_process:
            try:
                current_audio_process.terminate()
                current_audio_process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                current_audio_process.kill()
            except:
                pass
            current_audio_process = None