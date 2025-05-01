import cv2
import numpy as np
import zmq
class HotspotDetector:
    def __init__(self, camera_index=4):

        #Computer Vision Part
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise Exception("Could not open camera.")
        
        #Communication Part
        self.socket = None





context = zmq.Context()
socket = context.socket(zmq.PUB)  # PUB = Publisher mode
socket.bind("tcp://localhost:5555")  # Bind to a port


def detect_hotspots(frame, threshold=100, max_threshold=255):
    """
    Detects hotspots in an IR frame by applying thresholding and contour detection.
    """
    # Ensure frame is grayscale and properly formatted
    if len(frame.shape) == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = frame.astype(np.uint8)
    
    # Apply Gaussian blur to reduce noise
    #frame = cv2.GaussianBlur(frame, (5, 5), 2) # DOES NOT WORK WELL FOR IR
    
    # Apply thresholding to isolate hotspots
    contour_stack = []
    for current_threshold in range(threshold, max_threshold, 5):
        _, thresh = cv2.threshold(frame, current_threshold, 255, cv2.THRESH_BINARY)
    
        # Find contours of hotspots
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            contour_stack.append(contours)
    
    # Draw contours on the original frame
    brightest_contour = contour_stack.pop() if contour_stack else []
    output_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    cv2.drawContours(output_frame, brightest_contour, -1, (0, 0, 255), 2)
    
    return output_frame, brightest_contour, thresh

def main():
    """
    Captures video from an IR camera and detects hotspots in real time.
    """
    cap = cv2.VideoCapture(4)  # Use default IR camera
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    cv2.namedWindow("Hotspot Detection", cv2.WINDOW_NORMAL)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Detect hotspots
        processed_frame, contours, thresh = detect_hotspots(frame)
        
        # Get frame dimensions
        Y_dimension, X_dimension, _ = processed_frame.shape
        midpoint = X_dimension // 2
        
        # Define line sections for sectors
        line_section = np.concatenate(
            (
                np.linspace(0, X_dimension / 4, 5),
                np.linspace(X_dimension / 4, X_dimension / 2, 5),
                np.linspace(X_dimension / 2, 3 * X_dimension / 4, 5),
                np.linspace(3 * X_dimension / 4, X_dimension, 5)
            ), axis=0)
        line_section = np.unique(line_section)  # Remove duplicates
        
        # Draw sector lines
        for i, line_x in enumerate(line_section):
            line_x = int(line_x)
            cv2.line(img=processed_frame, pt1=(line_x, 0), pt2=(line_x, Y_dimension), color=(255, 0, 0), thickness=2)
        
        # Label detected hotspots with their sector
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            cx = x + w // 2  # Center x-coordinate of hotspot
            
            # Determine sector number
            sector_number = np.searchsorted(line_section, cx) - len(line_section) // 2
            
            # Draw text label near hotspot
            cv2.putText(processed_frame, f"Sector {sector_number}", (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            message = f"{sector_number}"
            print(f"Sending: {message}")
            socket.send_string(message)
        cv2.imshow("Hotspot Detection", processed_frame)
        
        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
