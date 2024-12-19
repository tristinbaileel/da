import cv2
import numpy as np
import time

class CircleDetector:
    def __init__(self):
        # FPS tracking
        self.circle_fps = 0
        self.frames_processed = 0
        self.last_time = time.perf_counter()
        self.fps_update_interval = 2.0
        
        # Pre-allocate grayscale buffer
        self.gray = np.zeros((30, 30), dtype=np.uint8)
        
        # Cache HoughCircles parameters
        self.hough_params = dict(
            method=cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=20,
            param1=20,
            param2=20,
            minRadius=3,
            maxRadius=8
        )
        
        self.target_fps = 150
        self.frame_time = 1.0 / self.target_fps

    def detect_circles(self, section):
        loop_start = time.perf_counter()
        
        # Convert to grayscale if needed, using pre-allocated buffer
        if len(section.shape) == 3:
            cv2.cvtColor(section, cv2.COLOR_BGR2GRAY, dst=self.gray)
            gray = self.gray
        else:
            gray = section

        # Apply Hough Circle Transform with cached parameters
        circles = cv2.HoughCircles(gray, **self.hough_params)

        # Update FPS calculation
        self.frames_processed += 1
        current_time = time.perf_counter()
        elapsed = current_time - self.last_time

        if elapsed >= self.fps_update_interval:
            self.circle_fps = self.frames_processed / elapsed
            self.frames_processed = 0
            self.last_time = current_time

        # Move FPS cap before returns
        elapsed = time.perf_counter() - loop_start
        if elapsed < self.frame_time:
            time.sleep(self.frame_time - elapsed)
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            return circles[0, :]
        return []