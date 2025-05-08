import cv2
import numpy as np
from scipy.optimize import curve_fit
import time
class HotspotDetector:
    def __init__(self, camera_index=4):

        #Computer Vision Part
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise Exception("Could not open camera.")
        
    def detect_hotspots_2(self,frame, threshold=100, max_threshold=255):
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
            valid_hotspots = []
            for cont in contours:
                if cv2.contourArea(cont) < 5 or cv2.contourArea(cont) > 250:
                    valid_hotspots.append(cont)
            if len(valid_hotspots) > 0:
                contour_stack.append(valid_hotspots)
        
        # Draw contours on the original frame
        brightest_contour = contour_stack.pop() if contour_stack else []
        output_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(output_frame, brightest_contour, -1, (0, 0, 255), 2)
        
        return output_frame, brightest_contour, thresh, contour_stack
    
    def exp_decay(self,x, a, b):
        return a * np.exp(-b * x)

    def detect_hotspots(self, frame, 
                        min_area=5,            # Minimum hotspot area in pixels
                        max_area=100,          # Maximum hotspot area in pixels
                        intensity_percentile=99.5,  # Top intensity percentile
                        contrast_threshold=20,      # Min center-surround contrast
                        circularity_threshold=0.7,  # Minimum circularity (0-1)
                        radial_samples=8,           # Number of radial directions
                        min_radial_decay=0.8):       # Min intensity decay factor
        """
        Detects IR hotspots with circularity and radial intensity checks.
        """
        frame = cv2.GaussianBlur(frame, (5, 5), cv2.BORDER_DEFAULT) # DOES NOT WORK WELL FOR IR
        # Preprocessing
        if len(frame.shape) == 3:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = frame.astype(np.uint8)

        # Adaptive thresholding
        threshold_value = np.percentile(frame, intensity_percentile)
        _, thresh = cv2.threshold(frame, threshold_value, 255, cv2.THRESH_BINARY)

        # Morphological cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        valid_hotspots = []
        output_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        for cnt in contours:
            # Size filtering
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue

            # Circularity check
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = (4 * np.pi * area) / (perimeter ** 2)
            if circularity < circularity_threshold:
                continue

            # Create mask and get centroid
            mask = np.zeros_like(frame)
            cv2.drawContours(mask, [cnt], -1, 255, -1)
            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # # Radial intensity decay check
            # if not self.validate_radial_decay(frame, (cx, cy), 
            #                                 min_decay=min_radial_decay,
            #                                 num_directions=radial_samples):
            #     continue

            # Contrast check with surroundings
            x,y,w,h = cv2.boundingRect(cnt)
            expanded_roi = frame[max(y-5,0):min(y+h+5,frame.shape[0]),
                                max(x-5,0):min(x+w+5,frame.shape[1])]
            if expanded_roi.size == 0:
                continue
                
            mean_hotspot = cv2.mean(frame, mask=mask)[0]
            mean_surround = cv2.mean(expanded_roi, 
                                    mask=cv2.bitwise_not(mask[max(y-5,0):min(y+h+5,frame.shape[0]),
                                                        max(x-5,0):min(x+w+5,frame.shape[1])]))[0]
            if (mean_hotspot - mean_surround) < contrast_threshold:
                continue

            valid_hotspots.append(cnt)
            cv2.drawContours(output_frame, [cnt], -1, (0,0,255), 2)

        return output_frame, valid_hotspots, thresh
    
    def detect_hotspots_fast(self,frame,threshold,min_area,max_area,circularity_threshold):
        if len(frame.shape) == 3:
            lower = np.array([230, 230, 230], dtype=np.uint8)
            upper = np.array([255, 255, 255], dtype=np.uint8)
            white_mask = cv2.inRange(frame, lower, upper)
            frame = cv2.bitwise_and(frame, frame, mask=white_mask)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame = cv2.GaussianBlur(frame, (21, 21), cv2.BORDER_DEFAULT)
        thresh_val = np.percentile(frame,threshold)
        binary = (frame >= thresh_val).astype(np.uint8) * 255
        #binary = cv2.medianBlur(binary,3)
        contours,_ = cv2.findContours(binary,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        hotspots = []
        for cont in contours:
            area = cv2.contourArea(cont)
            if area < min_area or area > max_area:
                continue
            perimeter = cv2.arcLength(cont,True)
            if perimeter == 0:
                continue
            circularity = (4 * np.pi * area) / (perimeter ** 2)
            if circularity < circularity_threshold:
                continue
            hotspots.append(cont)
        return binary,hotspots


    def validate_radial_decay(self, frame, center, min_decay=0.8, num_directions=8, steps=5):
        """
        Checks if intensity decreases radially from center in multiple directions
        """
        cx, cy = center
        valid_directions = 0
        height, width = frame.shape
        
        # Check multiple directions around the center
        for angle in np.linspace(0, 2*np.pi, num_directions, endpoint=False):
            intensities = []
            distances = []
            
            # Sample points along the radial direction
            for r in range(0, 15, 3):  # Check up to 15 pixels from center
                x = int(cx + r * np.cos(angle))
                y = int(cy + r * np.sin(angle))
                
                if 0 <= x < width and 0 <= y < height:
                    intensities.append(frame[y, x])
                    distances.append(r)
                else:
                    break
            
            # Check intensity decay profile
            if len(intensities) < 2:
                continue
                
            # Normalize intensities and distances
            max_intensity = max(intensities)
            if max_intensity == 0:
                continue
                
            normalized_intensity = [i/max_intensity for i in intensities]
            try:
                popt, _ = curve_fit(self.exp_decay, distances, normalized_intensity, bounds=(0, [1.5, 5]))
                decay_rate = popt[1]  # 'b' in the exponential
            except RuntimeError:
                decay_rate = 0
            if decay_rate > min_decay:
                valid_directions += 1
            #decay_factor = np.polyfit(distances, normalized_intensity, 1)[0]
            
            # Count as valid if intensity decreases with distance (negative slope)
            # if decay_factor < -min_decay/steps:
            #     valid_directions += 1

        # Require at least half directions show proper decay
        return valid_directions >= num_directions//2





    def return_frame(self):
        """
        Returns the current frame from the camera.
        """
        ret, frame = self.cap.read()
        if not ret:
            #raise Exception("Could not read frame from camera.")
            print("Error: Could not read frame from camera.")
            return None
        return frame

    
    


    def is_all_blue(self,frame, tolerance=10):
        # Check if pixels are close to pure blue (255, 0, 0)
        blue = np.array([255, 0, 0])
        diff = np.abs(frame.astype(int) - blue)
        mask = np.all(diff <= tolerance, axis=2)
        return np.mean(mask) > 0.98  # More than 98% pixels are blue

    def is_all_black(self,frame, threshold=10):
        return np.mean(frame) < threshold

    def is_static_noise(self, frame, laplacian_thresh=2000, hist_spike_thresh=0.4):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 1. Laplacian variance check
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        variance = laplacian.var()

        # 2. Histogram spike check (static often has uniform distribution)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        hist_normalized = hist / hist.sum()  # Normalize to 0-1
        max_spike = hist_normalized.max()

        # Static has both high variance AND no single dominant intensity
        return (variance > laplacian_thresh) and (max_spike < hist_spike_thresh)





    def validate_frame(self, frame): #check if the signal was good or something
       
        if self.is_static_noise(frame=frame,laplacian_thresh=260,hist_spike_thresh=10): 
            print("Error: Frame has static noise.")
            return False
        if self.is_all_blue(frame) or self.is_all_black(frame):
            print("Error: Frame is all blue or all black.")
            return False
        return True
    
    




    def return_valid_frame(self):
        """
        Returns a valid frame from the camera.
        """
        frame = self.return_frame()
        if self.validate_frame(frame):
            return frame
        else:
            print("Error: Invalid frame.")
            return None

    def return_valid_frame_blocking(self):
        """
        Returns a valid frame from the camera, blocking until a valid frame is available.
        """
        start_time = time.time()
        current_time = start_time
        while True:
            current_time = time.time()
            if current_time - start_time > 2.6:
                print("Error: No valid frames received within 5 seconds.")
                return None
            frame = self.return_valid_frame()
            if frame is not None:
                return frame


        

    


# def main():
#     """
#     Captures video from an IR camera and detects hotspots in real time.
#     """
#     cap = cv2.VideoCapture(4)  # Use default IR camera
    
#     if not cap.isOpened():
#         print("Error: Could not open camera.")
#         return
    
#     cv2.namedWindow("Hotspot Detection", cv2.WINDOW_NORMAL)
    
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
        
#         # Detect hotspots
#         processed_frame, contours, thresh = detect_hotspots(frame)
        
#         # Get frame dimensions
#         Y_dimension, X_dimension, _ = processed_frame.shape
#         midpoint = X_dimension // 2
        
#         # Define line sections for sectors
#         line_section = np.concatenate(
#             (
#                 np.linspace(0, X_dimension / 4, 5),
#                 np.linspace(X_dimension / 4, X_dimension / 2, 5),
#                 np.linspace(X_dimension / 2, 3 * X_dimension / 4, 5),
#                 np.linspace(3 * X_dimension / 4, X_dimension, 5)
#             ), axis=0)
#         line_section = np.unique(line_section)  # Remove duplicates
        
#         # Draw sector lines
#         for i, line_x in enumerate(line_section):
#             line_x = int(line_x)
#             cv2.line(img=processed_frame, pt1=(line_x, 0), pt2=(line_x, Y_dimension), color=(255, 0, 0), thickness=2)
        
#         # Label detected hotspots with their sector
#         for contour in contours:
#             x, y, w, h = cv2.boundingRect(contour)
#             cx = x + w // 2  # Center x-coordinate of hotspot
            
#             # Determine sector number
#             sector_number = np.searchsorted(line_section, cx) - len(line_section) // 2
            
#             # Draw text label near hotspot
#             cv2.putText(processed_frame, f"Sector {sector_number}", (x, y - 10), 
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

#             message = f"{sector_number}"
#             print(f"Sending: {message}")
#             socket.send_string(message)
#         cv2.imshow("Hotspot Detection", processed_frame)
        
#         # Exit on pressing 'q'
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
    
#     cap.release()
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     main()
