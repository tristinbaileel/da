import cv2
import numpy as np

class ColorDetector:
    def __init__(self):
        # Pre-compute color masks as uint8
        self.lower_purple = np.array([120, 0, 120], dtype=np.uint8)
        self.upper_purple = np.array([255, 50, 255], dtype=np.uint8)
        
        # Update mask size for new dimensions (half of 300x450)
        self.mask = np.zeros((225, 150), dtype=np.uint8)
        
    def detect_purple(self, section):
        # Downsample by taking every 2nd pixel
        downsampled = section[::2, ::2]
        
        # Use pre-allocated mask
        cv2.inRange(downsampled, self.lower_purple, self.upper_purple, 
                   dst=self.mask[:downsampled.shape[0], :downsampled.shape[1]])
        has_purple = np.any(self.mask[:downsampled.shape[0], :downsampled.shape[1]])
        
        return has_purple, section
