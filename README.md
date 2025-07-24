# desk-assistant
A repository to store all source code related to the UoS Robosoc Desk Assistant (Name TBC)
## Instructions 
You will need to host two servers, one for piper and one for ollama, whisper will run locally in your IDE

### 1. Install system dependencies
(Install ffmeg)
brew install ollama portaudio ffmpeg  # macOS
### or
sudo apt-get install portaudio19-dev python3-pyaudio alsa-utils ffmpeg  # Linux

### 2. Install Python dependencies
pip install -r requirements.txt

### 3. Pull the Ollama model
ollama pull mannix/llama3.1-8b-abliterated:latest

### 4. Start Piper TTS server (in separate terminal)
python3 -m piper.http_server -m en_GB-southern_english_female-low

### 5. Start Ollama server (in seperate terminal)
ollama serve

### 6. Run the main application
python main.py