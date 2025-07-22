"""Do pip install -r requirements.txt to install all dependencies"""
import ollama
import time
import os
import subprocess
import tempfile
from piper_tts import speak_with_piper, stop_audio #piper stored in another file
import queue
import threading

model = 'mannix/llama3.1-8b-abliterated:latest'

# System personality message
system_prompt = "You are a helpful assistant that replies briefly and clearly."

# Initialize conversation history
messages = [
    {'role': 'system', 'content': system_prompt}
]

def handle_conversation():
    print("Welcome to the AI chatbot! Type 'exit' to quit.")
    print("You can interrupt audio playback by typing a new message.\n")
    
    input_queue = queue.Queue()
    stop_event = threading.Event()
    
    def input_worker():
        while not stop_event.is_set():
            try:
                user_input = input("You: ")
                input_queue.put(user_input)
            except (EOFError, KeyboardInterrupt):
                input_queue.put("exit")
                break
 
    input_thread = threading.Thread(target=input_worker, daemon=True)
    input_thread.start()

    while True:
        # Get user input
        try:
            user_input = input_queue.get(timeout= 0.5)
        except:
            continue
        
        # Stop any currently playing audio, when a new input arrives
        stop_audio()
        
        # Check for exit
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        
        # Add user message to history
        messages.append({'role': 'user', 'content': user_input})
        
        # Capture response text
        response_text = ""
        
        print("Bot: ", end='')
        
        # Stream response
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
        
        # Add assistant response to history
        messages.append({'role': 'assistant', 'content': response_text})
        
        # Start audio playback in a separate thread
        audio_thread = threading.Thread(target=speak_with_piper, args=(response_text,), daemon=True)
        audio_thread.start()


def get_input_with_timeout():
    """Get user input with ability to detect when input is available"""
    input_queue = queue.Queue()
    
    def input_thread():
        try:
            user_input = input("You: ")
            input_queue.put(user_input)
        except EOFError:
            input_queue.put("exit")
    
    thread = threading.Thread(target=input_thread, daemon=True)
    thread.start()
    
    return input_queue


if __name__ == "__main__":
    handle_conversation()