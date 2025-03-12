import cv2
import numpy as np

def detect_hotspots(frame, threshold=150):
    """
    Detects hotspots in an IR frame by applying thresholding and contour detection.
    """
    # Ensure frame is grayscale and properly formatted
    if len(frame.shape) == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = frame.astype(np.uint8)
    
    # Apply Gaussian blur to reduce noise
    frame = cv2.GaussianBlur(frame, (5, 5), 2)
    
    # Apply thresholding to isolate hotspots
    _, thresh = cv2.threshold(frame, threshold, 150, cv2.THRESH_BINARY)
    
    # Find contours of hotspots
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw contours on the original frame
    output_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(output_frame, contours, -1, (0, 0, 255), 2)
    
    return output_frame, contours

def main():
    """
    Captures video from an IR camera and detects hotspots in real time.
    """
    cap = cv2.VideoCapture(2)  # Use default IR camera
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    cv2.namedWindow("Hotspot Detection", cv2.WINDOW_NORMAL)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect hotspots
        processed_frame, _ = detect_hotspots(frame)
        
        cv2.imshow("Hotspot Detection", processed_frame)
        
        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
