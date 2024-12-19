import bettercam
import cv2
import win32api
import time
import numpy as np
import threading

class ScreenCapture:
    def __init__(self):
        self.output_color = "BGR"
        self.target_fps = 150  # Cap at 150 FPS
        
        # Get screen dimensions
        self.screen_width = win32api.GetSystemMetrics(0)
        self.screen_height = win32api.GetSystemMetrics(1)
        
        # Pre-allocate frame buffer with new dimensions
        self.frame = np.zeros((450, 300, 3), dtype=np.uint8)  # height x width x channels
        
        # Calculate region with new dimensions
        width = 300
        height = 450
        left = (self.screen_width - width) // 2
        top = (self.screen_height - height) // 2
        self.region = (left, top, left + width, top + height)
        
        self.camera = self.create_camera()
        
        # Threading setup with FPS tracking
        self.frame = None
        self.running = False
        self.capture_fps = 0
        self.fps_update_interval = 2.0
        
    def create_camera(self):
        """Create bettercam instance with optimized settings"""
        camera = bettercam.create(
            output_color=self.output_color,
            max_buffer_len=2,  # Increased buffer for smoother capture
            device_idx=0
        )
        
        # Start capture with optimized settings
        camera.start(
            target_fps=self.target_fps, 
            video_mode=True, 
            region=self.region
        )
        return camera
    
    def set_color_mode(self, use_gray):
        """Switch between BGR and GRAY color modes"""
        self.output_color = "GRAY" if use_gray else "BGR"
        
        # Stop capture thread if running
        if self.running:
            self.running = False
            if hasattr(self, 'capture_thread'):
                self.capture_thread.join()
        
        # Properly cleanup old camera instance
        if hasattr(self, 'camera'):
            self.camera.release()
            del self.camera
        
        # Create new camera instance with FPS limit
        self.camera = self.create_camera()
        
        # Restart capture if it was running
        if hasattr(self, 'capture_thread'):
            self.running = True
            self.capture_thread = threading.Thread(target=self.capture_loop)
            self.capture_thread.start()
    
    def capture_loop(self):
        """Dedicated capture thread"""
        frames = 0
        start_time = time.perf_counter()
        frame_time = 1.0 / self.target_fps  # Time per frame at target FPS
        
        while self.running:
            loop_start = time.perf_counter()
            
            new_frame = self.camera.get_latest_frame()
            if new_frame is not None:
                self.frame = new_frame
                frames += 1
                
                # FPS tracking
                current_time = time.perf_counter()
                elapsed = current_time - start_time
                if elapsed >= self.fps_update_interval:
                    self.capture_fps = frames / elapsed
                    frames = 0
                    start_time = current_time
                
                # Cap FPS
                elapsed = time.perf_counter() - loop_start
                if elapsed < frame_time:
                    time.sleep(frame_time - elapsed)
    
    def start(self):
        """Start capture thread"""
        self.running = True
        self.capture_thread = threading.Thread(target=self.capture_loop)
        self.capture_thread.start()
    
    def stop(self):
        """Stop capture thread and release resources"""
        self.running = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join()
        self.camera.release()

    def get_frame(self):
        """Get the latest frame"""
        return self.frame

