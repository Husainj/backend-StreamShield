import os
from typing import Literal, Optional
from pydub import AudioSegment

from .video_processor import process_video, VideoBlurProcessor
from .audio_processor import load_bad_words, extract_audio, transcribe_audio, censor_audio
from .merge import merge_audio_video

ProcessOption = Literal['blur', 'beep_video', 'beep_audio']

class MediaProcessor:
    def __init__(self, model_path: str, badwords_path: str):
        self.model_path = model_path
        self.badwords_path = badwords_path
        self.blur_processor = VideoBlurProcessor(model_path)
        self.bad_words = load_bad_words(badwords_path)
        self.vosk_model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vosk-model-small-en-in-0.4")

    def process_media(self, input_path: str, output_path: str, process_option: ProcessOption) -> None:
        """Process media file based on the selected option."""
        
        is_video = self._is_video_file(input_path)
        
        if is_video:
            self._process_video_file(input_path, output_path, process_option)
        else:
            self._process_audio_file(input_path, output_path, process_option)

    def _is_video_file(self, file_path: str) -> bool:
        """Check if the file is a video file based on extension."""
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv'}
        _, ext = os.path.splitext(file_path.lower())
        return ext in video_extensions

    def _process_video_file(self, input_path: str, output_path: str, process_option: ProcessOption) -> None:
        """Process video file with the specified option."""
        temp_video = "temp_processed_video.mp4"
        temp_audio = "temp_processed_audio.wav"
        extracted_audio = extract_audio(input_path)
        
        try:
            if process_option == 'blur':
                # Only blur the video, keep original audio
                process_video(input_path, temp_video, self.blur_processor)
                merge_audio_video(temp_video, extracted_audio, output_path)
            
            elif process_option == 'beep_video':
                # Keep original video, only beep the audio
                audio = AudioSegment.from_wav(extracted_audio)
                transcription_data = transcribe_audio(extracted_audio, self.vosk_model_path)
                censored_audio, _ = censor_audio(audio, transcription_data, self.bad_words)
                censored_audio.export(temp_audio, format="wav")
                merge_audio_video(input_path, temp_audio, output_path)
            
            elif process_option == 'beep_audio':
                # Apply both video blur and audio beep
                process_video(input_path, temp_video, self.blur_processor)
                audio = AudioSegment.from_wav(extracted_audio)
                transcription_data = transcribe_audio(extracted_audio, self.vosk_model_path)
                censored_audio, _ = censor_audio(audio, transcription_data, self.bad_words)
                censored_audio.export(temp_audio, format="wav")
                merge_audio_video(temp_video, temp_audio, output_path)

        finally:
            # Clean up temporary files
            self._cleanup_temp_files([temp_video, temp_audio, extracted_audio])

    def _process_audio_file(self, input_path: str, output_path: str, process_option: ProcessOption) -> None:
        """Process audio file with the specified option."""
        if process_option in ['beep_audio', 'beep_video']:
            audio = AudioSegment.from_file(input_path)
            wav_path = "temp_audio.wav"
            audio.export(wav_path, format="wav", parameters=["-ac", "1", "-ar", "16000"])
            transcription_data = transcribe_audio(wav_path, self.vosk_model_path)
            censored_audio, _ = censor_audio(audio, transcription_data, self.bad_words)
            censored_audio.export(output_path, format="wav")
        else:
            # For 'blur' option on audio file, just copy the file
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format="wav")

    def _cleanup_temp_files(self, file_paths: list[str]) -> None:
        """Clean up temporary files if they exist."""
        for file_path in file_paths:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error removing temporary file {file_path}: {e}")
