import threading 
import queue
import time
import argparse
from sys import platform
from transcribe import RealTimeTranscriber

text_queue = queue.Queue()

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

threads = [
    threading.Thread(target=whisper_thread, daemon=True),
]

for thread in threads:
    thread.start()

# Keep main thread alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")