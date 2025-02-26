import os
import sys
from pydub import AudioSegment

from video_processor import process_video, VideoBlurProcessor
from audio_processor import load_bad_words, extract_audio, transcribe_audio, censor_audio
from merge import merge_audio_video

def process_video_and_audio(input_video_path: str, output_video_path: str, model_path: str, badwords_path: str):
    # Initialize video blur processor
    blur_processor = VideoBlurProcessor(model_path)

    # Process video
    processed_video_path = "processed_video.mp4"
    process_video(input_video_path, processed_video_path, blur_processor)

    # Process audio
    bad_words = load_bad_words(badwords_path)
    wav_file = extract_audio(input_video_path)
    audio = AudioSegment.from_wav(wav_file)
    transcription_data = transcribe_audio(wav_file, r"C:\Projects\Privacy Lens\server\StreamShield\vosk-model-small-en-in-0.4")
    censored_audio, _ = censor_audio(audio, transcription_data, bad_words)
    # processed_audio_path = merge_audio_with_video(input_video_path, censored_audio)

    # Save censored audio to a temporary file (required for ffmpeg)
    censored_audio_path = "temp_censored_audio.wav"
    censored_audio.export(censored_audio_path, format="wav")

    # Merge processed video and audio
    merge_audio_video(processed_video_path, censored_audio_path, output_video_path)

    # Clean up temporary files
    os.remove(processed_video_path)
    os.remove(censored_audio_path)
    os.remove(wav_file)

if __name__ == "__main__":
    # input_video_path = "C:/Users/jhalo/Downloads/rocktest.mp4"
    # output_video_path = "output.mp4"
    model_path = "best.pt"
    badwords_path = "static/badwords.txt"

    input_video_path = sys.argv[1]
    output_video_path = sys.argv[2]


    process_video_and_audio(input_video_path, output_video_path, model_path, badwords_path)

    print("Processed Successfully!!")