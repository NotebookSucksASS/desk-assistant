import threading 
import queue
import time
import argparse
from sys import platform
from transcribe import RealTimeTranscriber
import ollama
from piper_tts import speak_with_piper, stop_audio

text_queue = queue.Queue()
response_queue = queue.Queue()

model = 'mannix/llama3.1-8b-abliterated:latest'

# System personality message
system_prompt = "You are a helpful assistant that replies briefly and clearly."

# Initialize conversation history
messages = [
    {'role': 'system', 'content': system_prompt}
]

def transcription_callback(text):
    """Callback to handle completed transcriptions"""
    if text.strip():
        text_queue.put(text)
        print(f"Added to queue: {text}")

def whisper_thread():
    """Thread for running Whisper transcription"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="tiny", help="Model to use",
                        choices=["tiny", "base", "small", "medium", "large"])
    parser.add_argument("--non_english", action='store_true',
                        help="Don't use the english model.")
    parser.add_argument("--energy_threshold", default=1000,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=2,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=3,
                        help="How much empty space between recordings before we "
                             "consider it a new line in the transcription.", type=float)
    if 'linux' in platform:
        parser.add_argument("--default_microphone", default='pulse',
                            help="Default microphone name for SpeechRecognition. "
                                 "Run this with 'list' to view available Microphones.", type=str)
    args = parser.parse_args()
    
    # Create and run transcriber
    transcriber = RealTimeTranscriber(
        model=args.model,
        non_english=args.non_english,
        energy_threshold=args.energy_threshold,
        record_timeout=args.record_timeout,
        phrase_timeout=args.phrase_timeout,
        default_microphone=getattr(args, 'default_microphone', 'pulse'),
        transcription_callback= transcription_callback
    )
    transcriber.run()

def ollama_thread():
    
    while True:
        try:
            user_input = text_queue.get(timeout=0.5)
            
            # Stop any currently playing audio when new input arrives (from your main_tts.py)
            stop_audio()
            
            if user_input.lower() == "exit":
                print("Goodbye!")
                break
            
            # Add user message to history 
            messages.append({'role': 'user', 'content': user_input})
            
            # Capture response text 
            response_text = ""
            
            print("🤖 Bot: ", end='')

            stream = ollama.chat(
                model=model,
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                text = chunk['message']['content']
                print(text, end='')
                response_text += text
            
            print()  # New line after response
            
            # Add assistant response to history (from your main_tts.py)
            messages.append({'role': 'assistant', 'content': response_text})
            
            # Add to TTS queue
            if response_text.strip():
                response_queue.put(response_text)
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"🚨 Ollama error: {e}")
        
        time.sleep(0.1)

def piper_thread():
    while True:
        try:
            response = response_queue.get(timeout= 0.5)
            speak_with_piper(response, )
        except queue.Empty:
            continue
        except Exception as e:
            print(f"🚨 TTS error: {e}")
        
        time.sleep(0.1)

threads = [
    threading.Thread(target=whisper_thread, daemon=True),        
    threading.Thread(target=ollama_thread, daemon=True),
    threading.Thread(target = piper_thread, daemon=True)
]

for thread in threads:
    thread.start()

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")