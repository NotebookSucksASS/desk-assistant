import os
import subprocess
import tempfile


def speak_with_piper(text):
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file: 
        temp_wav = temp_file.name
    
    # Generate speech with Piper
    model_path = "./assets/en_GB-southern_english_female-low"

    subprocess.run(['python3', '-m', 'piper', '--model', model_path, '--output_file', temp_wav],
                   input=text, text=True)

    # Play audio
    if os.name == 'posix':  # Linux/Mac
        os.system(f'aplay {temp_wav}' if os.system('which aplay > /dev/null 2>&1') == 0 else f'afplay {temp_wav}')
    else:  # Windows
        os.system(f'start {temp_wav}')
    
    os.unlink(temp_wav) 

