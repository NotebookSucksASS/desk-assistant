import os
import requests
import tempfile

def speak_with_piper(text, server_url="http://localhost:5000"):
    """
    Speak text using Piper TTS HTTP server
    
    Args:
        text (str): Text to speak
        server_url (str): URL of the Piper HTTP server (default: http://localhost:5000)
    """
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
                for chunk in response.iter_content(chunk_size=128):
                    f.write(chunk)
            
            # Play audio
            if os.name == 'posix':  # Linux/Mac
                # Check if aplay exists (Linux), otherwise use afplay (Mac)
                if os.system('which aplay > /dev/null 2>&1') == 0:
                    os.system(f'aplay {temp_wav}')
                else:
                    os.system(f'afplay {temp_wav}')
            else:  # Windows
                os.system(f'start {temp_wav}')
            
            # Clean up temp file
            os.unlink(temp_wav)
            
        else:
            print(f"Error from Piper server: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to Piper server. Make sure it's running on", server_url)
    except Exception as e:
        print(f"Error: {e}")
        # Clean up temp file if it exists
        if 'temp_wav' in locals() and os.path.exists(temp_wav):
            os.unlink(temp_wav)