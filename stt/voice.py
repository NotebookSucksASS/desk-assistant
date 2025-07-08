import wave
import sys

import pyaudio

class AudioRecorder:
    def __init__(self, chunk = 1024, format = pyaudio.paInt16, channels = 1 if sys.platform == 'darwin' else 2, rate = 44100):
        self.chunk = chunk
        self.format = format
        self.channels = channels
        self.rate = rate

    def record(self, filename, seconds):
        p = pyaudio.PyAudio()

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(p.get_sample_size(self.format))
            wf.setframerate(self.rate)
            
            stream = p.open(format=self.format, channels=self.channels, 
                          rate=self.rate, input=True)
            
            print('Recording...')
            for _ in range(0, self.rate // self.chunk * seconds):
                wf.writeframes(stream.read(self.chunk))
            print('Done')
            
            stream.close()
        
        p.terminate()
        
    