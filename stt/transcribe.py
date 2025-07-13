import argparse
import os
import numpy as np
import speech_recognition as sr
import whisper
import torch
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform


class RealTimeTranscriber:
    def __init__(self, model="tiny", non_english=False, energy_threshold=1000, 
                 record_timeout=2, phrase_timeout=2, default_microphone='pulse'):
        self.model_name = model
        self.non_english = non_english
        self.energy_threshold = energy_threshold
        self.record_timeout = record_timeout
        self.phrase_timeout = phrase_timeout
        self.default_microphone = default_microphone
        
        # State variables
        self.phrase_time = None # The last time a recording was retrieved from the queue.
        self.data_queue = Queue() # Thread safe Queue for passing data from the threaded recording callback.
        self.phrase_bytes = bytes() # Bytes object which holds audio data for the current phrase
        self.transcription = ['']
        self.stop_listening = None
        self.phrase_complete = False
        self.first_phrase_completed = False #Constant check of phrase complete, so need a flag to prevent running more than once
        
        # Initialize components
        self.recorder = None 
        self.source = None
        self.audio_model = None
        
    def setup_microphone(self):
        """Initialize microphone source"""
        if 'linux' in platform:
            if not self.default_microphone or self.default_microphone == 'list':
                print("Available microphone devices are: ")
                for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    print(f"Microphone with name \"{name}\" found")
                return False
            else:
                for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    if self.default_microphone in name:
                        self.source = sr.Microphone(sample_rate=16000, device_index=index)
                        break
                else:
                    raise ValueError(f"Microphone '{self.default_microphone}' not found")
        else:
            self.source = sr.Microphone(sample_rate=16000)
        return True
    
    def setup_recorder(self):
        """Initialize speech recognizer"""
        self.recorder = sr.Recognizer()
        self.recorder.energy_threshold = self.energy_threshold
        self.recorder.dynamic_energy_threshold = False
        
        # Adjust for ambient noise
        with self.source:
            self.recorder.adjust_for_ambient_noise(self.source)
    
    def load_model(self):
        """Load Whisper model"""
        model = self.model_name
        if self.model_name != "large" and not self.non_english:
            model = model + ".en"
        self.audio_model = whisper.load_model(model)
        print("Model loaded.\n")
    
    def record_callback(self, _, audio: sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        """
        data = audio.get_raw_data()
        self.data_queue.put(data)
    
    def start_listening(self):
        """Start background audio recording"""
        self.stop_listening = self.recorder.listen_in_background(
            self.source, 
            self.record_callback, 
            phrase_time_limit=self.record_timeout
        )
    
    def stop_recording(self):
        """Stop background audio recording"""
        if self.stop_listening:
            self.stop_listening()
            self.stop_listening = None
    
    def process_audio_queue(self):
        """Process audio data from the queue and transcribe"""
        if self.data_queue.empty():
            return False
        now = datetime.utcnow()

        self.phrase_time = now
        
        # Combine audio data from queue
        audio_data = b''.join(self.data_queue.queue)
        self.data_queue.queue.clear()
        
        # Add new audio data to accumulated phrase data
        self.phrase_bytes += audio_data
        
        # Convert to numpy array for Whisper
        audio_np = np.frombuffer(self.phrase_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        # Transcribe audio
        result = self.audio_model.transcribe(audio_np, fp16=torch.cuda.is_available())
        text = result['text'].strip()
        
        # Update transcription
        if self.phrase_complete:
            self.transcription.append(text)
        else:
            self.transcription[-1] = text
        
        return True
    
    def check_phrase_complete(self): #Check if user finished prompt
        now = datetime.utcnow()

        self.phrase_complete = False
        
        # Check if enough time has passed to consider phrase complete
        if self.phrase_time and now - self.phrase_time > timedelta(seconds=self.phrase_timeout): #Check if user has not spoken for more than phrase timeout (3s)
            self.phrase_bytes = bytes()
            self.phrase_complete = True
        
        if self.phrase_complete:
            return True
        else: 
            return False

    
    def display_transcription(self):
        """Clear screen and display current transcription"""
        os.system('cls' if os.name == 'nt' else 'clear')
        for line in self.transcription:
            print(line)
        print('', end='', flush=True)
    
    def run(self):
        """Main transcription loop"""
        try:
            # Setup components
            if not self.setup_microphone():
                return
            self.setup_recorder()
            self.load_model()
            self.start_listening()
            
            # Main processing loop
            while True:
                try:
                    print(self.check_phrase_complete())
                    if self.check_phrase_complete(): #Check if 2 seconds has passed since last speech
                        if self.first_phrase_completed == False: #Prevent bottom code running more than once
                            self.stop_recording()
                            filename = f"prompt_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt" #Save prompt as txt
                            with open(f"stt/prompts/{filename}", "w") as f:
                                f.write(self.transcription[-1])
                            input("Prompt recorded, press enter to continue")
                            self.start_listening()
                            self.phrase_complete = False #Reset variables for next prompts
                            self.phrase_time = None
                            self.first_phrase_completed = False
                            continue 
                        self.first_phrase_completed = True #Prevent code running more than once

                    if self.process_audio_queue() and not self.check_phrase_complete():
                        self.display_transcription()
                    else:
                        sleep(0.25)
                except KeyboardInterrupt:
                    break
                    
        finally:
            self.stop_recording()
            
        # Final transcription output
        print("\n\nTranscription:")
        for line in self.transcription:
            print(line)
    
    def get_transcription(self):
        """Get current transcription as list of strings"""
        return self.transcription.copy()
    
    def clear_transcription(self):
        """Clear current transcription"""
        self.transcription = ['']


def main():
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
        default_microphone=getattr(args, 'default_microphone', 'pulse')
    )
    
    transcriber.run()


if __name__ == "__main__":
    main()