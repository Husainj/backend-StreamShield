import wave
import json
import os
import subprocess
from vosk import Model, KaldiRecognizer
from pydub import AudioSegment
from pydub.generators import Sine

def load_bad_words(filepath):
    """Loads bad words from a file."""
    try:
        with open(filepath, "r") as f:
            return set(word.strip().lower() for word in f.readlines())
    except Exception as e:
        print(f"Error loading bad words file: {e}")
        exit(1)

def extract_audio(input_file):
    """Extracts audio from MP4 and converts it to WAV (16kHz mono)."""
    temp_wav = "temp_audio.wav"

    if input_file.endswith(".wav"):
        return input_file  # No need to convert WAV

    print(f"Extracting and converting {input_file} audio to WAV format...")
    subprocess.run(["ffmpeg", "-i", input_file, "-ac", "1", "-ar", "16000", "-vn", temp_wav, "-y"], check=True)
    return temp_wav

def transcribe_audio(audio_file, model_path):
    """Transcribes audio using Vosk."""
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)
    transcription_data = []
    try:
        with wave.open(audio_file, "rb") as wf:
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    transcription_data.extend(result.get("result", []))
        final_result = json.loads(recognizer.FinalResult())
        transcription_data.extend(final_result.get("result", []))
        print("Transcription data : " , transcription_data)
    except Exception as e:
        print(f"Error during transcription: {e}")
        exit(1)


    return transcription_data

def censor_audio(audio, transcription_data, bad_words):
    """Applies beep sound over detected bad words."""
    censored_transcript = []
    for word in transcription_data:
        word_text = word["word"].lower()
        if word_text in bad_words:
            start_time = int(word["start"] * 1000)
            end_time = int(word["end"] * 1000)
            word_duration = end_time - start_time
            beep = Sine(1000).to_audio_segment(duration=word_duration).apply_gain(-5)
            audio = audio[:start_time] + beep + audio[end_time:]
            censored_transcript.append(f"[{word['start']:.2f}s - {word['end']:.2f}s] {word['word']}")
    return audio, censored_transcript

