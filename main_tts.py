"""Do pip install -r requirements.txt to install all dependencies"""
import ollama
import time
import os
import subprocess
import tempfile
from piper_tts import speak_with_piper #piper stored in another file

model = 'mannix/llama3.1-8b-abliterated:latest'

# System personality message
system_prompt = "You are a helpful assistant that replies briefly and clearly."

# Initialize conversation history
messages = [
    {'role': 'system', 'content': system_prompt}
]

def handle_conversation():
    print("Welcome to the AI chatbot! Type 'exit' to quit.")
    
    while True:
        # Get user input
        user_input = input("You: ")
        
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
        
        speak_with_piper(response_text)

if __name__ == "__main__":
    handle_conversation()