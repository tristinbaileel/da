import win32api
import win32con
import math
import time
import numpy as np

class MouseMover:
    def __init__(self):
        # Screen setup
        self.screen_width = win32api.GetSystemMetrics(0)
        self.screen_height = win32api.GetSystemMetrics(1)
        self.screen_center_x = self.screen_width // 2
        self.screen_center_y = self.screen_height / 2.16 #used to be 2.19 2.16 is better    
        
        # Pre-allocate arrays for calculations
        self.coords = np.zeros(2, dtype=np.float32)
        self.movement = np.zeros(2, dtype=np.float32)
        
        # Movement settings
        self.tracking_speed_x = 5
        self.tracking_speed_y = 5
        self.deadzone = 14  # used to be 3 14 is better
        self.aa_enabled = False
        
        # Target height ratios
        self.height_ratios = {
            'head': 2.16,
            'chest': 2.22,
            'belly': 2.30,
            'feet': 2.38
        }
    
    def set_target_height(self, position):
        """Set the Y center based on target position"""
        if position in self.height_ratios:
            self.screen_center_y = self.screen_height / self.height_ratios[position]
    
    def toggle_aim_assist(self):
        """Toggle aim assist on/off"""
        self.aa_enabled = not self.aa_enabled
        return self.aa_enabled
    
    def process_aim_assist(self, target_x, target_y):
        """Process aim assist movement towards target using relative coordinates"""
        if not self.aa_enabled:
            return False
            
        try:
            # Use pre-allocated arrays
            self.coords[0] = target_x
            self.coords[1] = target_y
            total_distance = np.linalg.norm(self.coords)
            
            if total_distance > self.deadzone:
                np.multiply(self.coords / total_distance, 
                          [self.tracking_speed_x, self.tracking_speed_y], 
                          out=self.movement)
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE,
                                   int(round(self.movement[0])), 
                                   int(round(self.movement[1])), 
                                   0, 0)
                return True
            return False
            
        except Exception as e:
            print(f"Mouse movement error: {e}")
            return False
    
    def convert_capture_to_relative_coords(self, capture_x, capture_y):
        """Convert coordinates from 300x450 capture to relative coordinates"""
        # Convert from capture coordinates to screen coordinates first
        screen_x = capture_x + (self.screen_width - 300) // 2  # Updated width
        screen_y = capture_y + (self.screen_height - 450) // 2  # Updated height
        
        # Calculate relative to center point
        relative_x = screen_x - self.screen_center_x
        relative_y = screen_y - self.screen_center_y
        
        return relative_x, relative_y