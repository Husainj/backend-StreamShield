import cv2
from ultralytics import YOLO
from typing import List, Tuple


class VideoBlurProcessor:
    """Process videos to blur sensitive regions using YOLO object detection."""

    def __init__(
            self,
            model_path: str,
            blur_classes: List[int] = [2, 3],  # Default: class IDs for "login form" and "URL bar"
            confidence_threshold: float = 0.7,
            blur_kernel: Tuple[int, int] = (99, 99),
            blur_sigma: int = 30
    ):
        self.model = YOLO(model_path)
        self.blur_classes = blur_classes
        self.confidence_threshold = confidence_threshold
        self.blur_kernel = blur_kernel
        self.blur_sigma = blur_sigma

    def process_frame(self, frame) -> None:
        """Detect and blur regions in a single frame."""
        results = self.model(frame)
        for result in results:
            for box in result.boxes:
                if self._is_valid_detection(box):
                    self._apply_blur(frame, box)

    def _is_valid_detection(self, box) -> bool:
        """Check if detection meets confidence and class criteria."""
        confidence = box.conf[0].item()
        class_id = int(box.cls[0].item())
        return (confidence > self.confidence_threshold) and (class_id in self.blur_classes)

    def _apply_blur(self, frame, box) -> None:
        """Apply Gaussian blur to a detected region."""
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        roi = frame[y1:y2, x1:x2]
        blurred_roi = cv2.GaussianBlur(roi, self.blur_kernel, self.blur_sigma)
        frame[y1:y2, x1:x2] = blurred_roi