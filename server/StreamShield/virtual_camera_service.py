import cv2
import threading
import pyvirtualcam
import time
import os
import numpy as np
from typing import Optional
from mss import mss
from PIL import Image
from .video_processor.blur_processor import VideoBlurProcessor

class VirtualCameraService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.is_running = False
            self.processor: Optional[VideoBlurProcessor] = None
            self.virtual_cam: Optional[pyvirtualcam.Camera] = None
            self.processing_thread: Optional[threading.Thread] = None
            
            # Default screen capture settings
            self.width = 1920  # Full HD width
            self.height = 1080  # Full HD height
            self.fps = 30
            
            # Get the model path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            self.model_path = os.path.join(current_dir, "best.pt")

    def start(self) -> dict:
        """Start the virtual camera service with screen capture"""
        if self.is_running:
            return {"status": "error", "message": "Virtual camera is already running"}

        try:
            # Initialize blur processor
            self.processor = VideoBlurProcessor(self.model_path)

            # Initialize virtual camera
            self.virtual_cam = pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                fmt=pyvirtualcam.PixelFormat.BGR
            )

            # Start processing thread
            self.is_running = True
            self.processing_thread = threading.Thread(target=self._process_screen, daemon=True)
            self.processing_thread.start()

            return {"status": "success", "message": "Virtual camera started successfully"}
        except Exception as e:
            self.stop()
            return {"status": "error", "message": f"Failed to start virtual camera: {str(e)}"}

    def stop(self) -> dict:
        """Stop the virtual camera service"""
        if not self.is_running:
            return {"status": "error", "message": "Virtual camera is not running"}

        try:
            self.is_running = False
            
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5.0)  # Wait up to 5 seconds
                
            if self.virtual_cam:
                self.virtual_cam.close()
                
            self.virtual_cam = None
            self.processor = None
            self.processing_thread = None

            return {"status": "success", "message": "Virtual camera stopped successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to stop virtual camera: {str(e)}"}

    def _process_screen(self):
        """Capture screen, process frames, and send to virtual camera"""
        with mss() as sct:
            # Define the screen region to capture (full screen)
            monitor = sct.monitors[1]  # Primary monitor
            
            while self.is_running:
                try:
                    # Capture screen
                    frame = np.array(sct.grab(monitor))
                    
                    # Convert from BGRA to BGR
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    # Resize if needed
                    if frame.shape[:2] != (self.height, self.width):
                        frame = cv2.resize(frame, (self.width, self.height))
                    
                    # Process frame using blur processor
                    self.processor.process_frame(frame)
                    
                    # Send to virtual camera
                    self.virtual_cam.send(frame)
                    self.virtual_cam.sleep_until_next_frame()
                except Exception as e:
                    print(f"Error processing frame: {str(e)}")
                    time.sleep(1/self.fps)  # Prevent busy-waiting on error

# Create singleton instance
virtual_camera_service = VirtualCameraService()
