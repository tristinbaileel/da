import numpy as np
import cv2
import time
import threading
from screen_grab import ScreenCapture
from color_detect import ColorDetector
from circle_detect import CircleDetector

class FrameProcessor:
    def __init__(self):
        self.screen_cap = ScreenCapture()
        self.color_detector = ColorDetector()
        self.circle_detector = CircleDetector()
        
        # Performance metrics
        self.process_fps = 0
        self.frames_processed = 0
        self.last_time = time.perf_counter()
        self.fps_print_interval = 2.0
        self.last_fps_print = time.perf_counter()
        
        # Pre-allocate buffers with new dimensions
        self.gray_region = np.zeros((30, 30), dtype=np.uint8)
        self.mask = np.zeros((450, 300), dtype=np.uint8)
        
        # Frame center point for new dimensions
        self.center_x = 150  # 300/2
        self.center_y = 225  # 450/2
        
        # Tracking state
        self.tracking_circle = False
        self.last_circle_center = None
        self.tracking_lost_frames = 0
        self.max_lost_frames = 5
        
        self.target_fps = 150
        self.frame_time = 1.0 / self.target_fps
        
        # Pre-allocate buffers for get_purple_regions
        self.purple_mask = np.zeros((450, 300), dtype=np.uint8)  # Full frame size
        self.moments = dict(m00=0.0, m10=0.0, m01=0.0)  # Pre-allocate moments dictionary
        self.tracking_region = np.zeros((30, 30, 3), dtype=np.uint8)  # For 30x30 regions
        
    def start(self):
        self.screen_cap.start()
    
    def process_frame(self, frame):
        loop_start = time.perf_counter()
        
        if frame is None:
            return
        
        circles_found = []
        
        # If we're tracking a circle, check that region first
        if self.tracking_circle and self.last_circle_center is not None:
            last_x, last_y = self.last_circle_center
            region, (cx, cy) = self.get_tracking_region(frame, last_x, last_y)
            
            if region is not None:
                # Convert region to grayscale for circle detection
                gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
                
                # Check if the region still contains purple
                mask = cv2.inRange(region, self.color_detector.lower_purple, self.color_detector.upper_purple)
                if np.any(mask):
                    # Try to detect circle in the region
                    circles = self.circle_detector.detect_circles(gray_region)
                    
                    if len(circles) > 0:
                        # Circle still detected, update tracking
                        x, y, r = circles[0]
                        adjusted_x = cx + int(x) - 15
                        adjusted_y = cy + int(y) - 15
                        circles_found.append((adjusted_x, adjusted_y, r))
                        self.last_circle_center = (adjusted_x, adjusted_y)
                        self.tracking_lost_frames = 0
                        return circles_found
            
            # If we reach here, circle wasn't found in tracking region
            self.tracking_lost_frames += 1
            
            # If we've lost tracking for too many frames, reset tracking
            if self.tracking_lost_frames >= self.max_lost_frames:
                self.tracking_circle = False
                self.last_circle_center = None
        
        # If we're not tracking or lost tracking, search for new purple regions
        if not self.tracking_circle:
            purple_regions = self.get_purple_regions(frame)
            
            for _, region, (cx, cy) in purple_regions:
                # Convert region to grayscale for circle detection
                gray_region = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
                
                # Detect circles in region
                circles = self.circle_detector.detect_circles(gray_region)
                
                if len(circles) > 0:
                    # Found a new circle to track
                    x, y, r = circles[0]
                    adjusted_x = cx + int(x) - 15
                    adjusted_y = cy + int(y) - 15
                    circles_found.append((adjusted_x, adjusted_y, r))
                    
                    # Start tracking this circle
                    self.tracking_circle = True
                    self.last_circle_center = (adjusted_x, adjusted_y)
                    self.tracking_lost_frames = 0
                    break
        
        # Update FPS metrics
        self.frames_processed += 1
        current_time = time.perf_counter()
        
        if current_time - self.last_fps_print >= self.fps_print_interval:
            self.process_fps = self.frames_processed / (current_time - self.last_time)
            print(f"\n=== Performance Metrics ===")
            print(f"Processing FPS: {self.process_fps:.1f}")
            print(f"Capture FPS: {self.screen_cap.capture_fps:.1f}")
            print(f"Circle Detection FPS: {self.circle_detector.circle_fps:.1f}")
            print("========================\n")
            
            self.frames_processed = 0
            self.last_time = current_time
            self.last_fps_print = current_time
        
        # Cap FPS
        elapsed = time.perf_counter() - loop_start
        if elapsed < self.frame_time:
            time.sleep(self.frame_time - elapsed)
        
        return circles_found
    
    def get_purple_regions(self, frame):
        """Find purple regions and return 30x30 sections sorted by distance to center"""
        # Use pre-allocated mask
        cv2.inRange(frame, self.color_detector.lower_purple, self.color_detector.upper_purple, 
                    dst=self.purple_mask)
        
        # Find contours of purple regions
        contours, _ = cv2.findContours(self.purple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours:
            # Get center of contour using pre-allocated moments
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Get 30x30 region around center using pre-allocated buffer
                region, center = self.get_tracking_region(frame, cx, cy)
                if region is not None:
                    # Calculate distance to frame center
                    dist = np.sqrt((cx - self.center_x)**2 + (cy - self.center_y)**2)
                    regions.append((dist, region, center))
        
        # Sort regions by distance to center
        regions.sort(key=lambda x: x[0])
        return regions
    
    def get_tracking_region(self, frame, cx, cy):
        """Get a 30x30 region around the given center point"""
        # Calculate region bounds
        x1 = max(0, cx - 15)
        y1 = max(0, cy - 15)
        x2 = min(frame.shape[1], cx + 15)
        y2 = min(frame.shape[0], cy + 15)
        
        # Check if we have a valid region size
        if x2 - x1 < 5 or y2 - y1 < 5:  # Minimum size check
            return None, (cx, cy)
        
        # Copy to pre-allocated buffer
        region_height = y2 - y1
        region_width = x2 - x1
        self.tracking_region[:region_height, :region_width] = frame[y1:y2, x1:x2]
        
        return self.tracking_region[:region_height, :region_width], (cx, cy)