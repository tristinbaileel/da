import bettercam
import cv2
import time

def main():
    try:
        # Create camera instance
        camera = bettercam.create()
        
        # Define left corner region (x1, y1, x2, y2)
        # For example, a 640x360 region in the top-left corner
        region = (0, 0, 640, 360)
        
        # Capture the specific region
        frame = camera.grab(region=region)
        
        if frame is not None:
            # Save the frame
            cv2.imwrite('left_corner_capture.png', frame)
            print("Screenshot saved as 'left_corner_capture.png'")
        else:
            print("Failed to capture frame")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        del camera

if __name__ == "__main__":
    main()