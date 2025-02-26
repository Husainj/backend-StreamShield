import subprocess

def merge_audio_video(processed_video_path: str, censored_audio_path: str, output_video_path: str):
    # Use ffmpeg to merge processed video and censored audio into the final output
    merge_cmd = [
        'ffmpeg', '-y',
        '-i', processed_video_path,  # Processed video
        '-i', censored_audio_path,  # Censored audio
        '-c:v', 'copy',  # Copy video stream without re-encoding
        '-c:a', 'aac',  # Encode audio in AAC format
        '-map', '0:v:0',  # Use video from the first input
        '-map', '1:a:0',  # Use audio from the second input
        output_video_path  # Final output file
    ]
    subprocess.run(merge_cmd, check=True)



