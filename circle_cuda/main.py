# main.py
import time
from line_profiler import profile
import signal
import sys
from splitter import FrameProcessor
from mm import MouseMover
import threading
import win32api
import win32process
import win32con
import psutil
import ctypes

def set_process_priorities():
    # Set CPU priority to high
    pid = win32api.GetCurrentProcessId()
    handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
    win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)
    
    # Set process CPU affinity to use all cores
    process = psutil.Process()
    process.cpu_affinity(list(range(psutil.cpu_count())))
    
    try:
        # Try to set GPU priority through Windows Graphics Settings
        process.nice(psutil.HIGH_PRIORITY_CLASS)
    except Exception as e:
        print(f"Could not set process priority: {e}")

@profile
def main():
    # Set process priorities
    set_process_priorities()
    
    processor = FrameProcessor()
    processor.start()
    mouse = MouseMover()

    def signal_handler(sig, frame):
        print("\nCleaning up...")
        processor.screen_cap.stop()
        sys.exit(0)

    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Add keyboard event checking thread
    def check_keyboard():
        from pynput import keyboard
        
        def on_press(key):
            try:
                if key.char == 'o':  # Toggle on 'o' key press
                    enabled = mouse.toggle_aim_assist()
                    print(f"\nAim Assist {'Enabled' if enabled else 'Disabled'}")
            except AttributeError:
                pass
        
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
    
    # Start keyboard listener in separate thread
    keyboard_thread = threading.Thread(target=check_keyboard)
    keyboard_thread.daemon = True  # Thread will close with main program
    keyboard_thread.start()

    frame_counter = 0
    debug_print_interval = 60  # Print every 60 frames
    
    target_fps = 150
    frame_time = 1.0 / target_fps
    
    try:
        while True:
            loop_start = time.perf_counter()
            
            frame = processor.screen_cap.get_frame()
            if frame is not None:
                circles = processor.process_frame(frame)
                if circles:
                    x, y, r = circles[0]
                    rel_x, rel_y = mouse.convert_capture_to_relative_coords(x, y)
                    mouse.process_aim_assist(rel_x, rel_y)
            
            # Cap FPS
            elapsed = time.perf_counter() - loop_start
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)
    except KeyboardInterrupt:
        print("\nCleaning up...")
        processor.screen_cap.stop()
    except Exception as e:
        print(f"Error: {e}")
        processor.screen_cap.stop()
        raise

if __name__ == '__main__':
    main()