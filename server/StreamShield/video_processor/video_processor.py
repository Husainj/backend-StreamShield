import cv2
from typing import Optional, Callable
from .blur_processor import VideoBlurProcessor


def process_video(
        input_path: str,
        output_path: str,
        processor: VideoBlurProcessor,
        progress_callback: Optional[Callable[[float], None]] = None) -> None:
    """Process an entire video and save the blurred output."""
    cap = cv2.VideoCapture(input_path)
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Initialize video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            processor.process_frame(frame)
            out.write(frame)
            if progress_callback:
                progress_callback(cap.get(cv2.CAP_PROP_POS_FRAMES) / cap.get(cv2.CAP_PROP_FRAME_COUNT))
    finally:
        cap.release()
        out.release()
        cv2.destroyAllWindows()