import cv2
import numpy as np
# Initialize the webcam
cap = cv2.VideoCapture(1)

while True:
    # Capture a frame from the webcam
    ret, frame = cap.read()

    if not ret:
        print("No frame captured")
        break

    # Convert to HSV color space for better red detection
    #hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Define the range of red colors in HSV
    #lower_red = np.array([0, 70, 50])
    #upper_red = np.array([10, 255, 255])
    #lower_red_high = np.array([0, 70, 50])
    #upper_red_high = np.array([20, 255, 255])

    #mask1 = cv2.inRange(hsv, lower_red, upper_red)
    #mask2 = cv2.inRange(hsv, lower_red_high, upper_red_high)
    # Bright Red
    lower_bright_red = np.array([0, 0, 120])  # More relaxed on red detection  
    upper_bright_red = np.array([120, 120, 255])  # Allow broader variations in B & G  

    mask_red = cv2.inRange(frame, lower_bright_red, upper_bright_red)

    # Mask for white (255, 255, 255)
    lower_white = np.array([100, 100, 100])  # Threshold for white
    upper_white = np.array([255, 255, 255])
    mask_white = cv2.inRange(frame, lower_white, upper_white)

    # Mask for grey (same R, G, and B values)
    lower_grey = np.array([100, 100, 100])  # Low grey
    upper_grey = np.array([180, 180, 180])  # High grey
    mask_grey = cv2.inRange(frame, lower_grey, upper_grey)

    # Combine the white and grey masks
    mask_remove_white_grey = cv2.bitwise_or(mask_white, mask_grey)

    kernel = np.ones((12, 12), np.uint8)

    #mask_remove_white_grey = cv2.erode(mask_remove_white_grey, kernel, iterations=3)  # Erode to remove small, thin streaks
    #mask_remove_white_grey = cv2.dilate(mask_remove_white_grey, kernel, iterations=3) 
    #mask_remove_white_grey = cv2.morphologyEx(mask_remove_white_grey, cv2.MORPH_CLOSE, kernel)

    # Remove white and grey by inverting the mask and combining it with the red mask
    mask_total = cv2.bitwise_and(mask_red, cv2.bitwise_not(mask_remove_white_grey))


# Dark Red (to be excluded if unwanted)
    #lower_dark_red = np.array([0, 0, 100])  
    #upper_dark_red = np.array([80, 80, 255])  

   
    #mask2 = cv2.inRange(frame, lower_dark_red, upper_dark_red)

    #mask_total = cv2.bitwise_or(mask1, mask2)  # Combine both

    

    # Combine the masks using bitwise OR to capture both red regions
    #mask_total = cv2.bitwise_or(mask1, mask2)

    
    mask_total = cv2.morphologyEx(mask_total, cv2.MORPH_CLOSE, kernel)

    #mask_total = cv2.erode(mask_total, kernel, iterations=2)  # Erode to remove small, thin streaks
    #mask_total = cv2.dilate(mask_total, kernel, iterations=2) 
    # Apply the mask to get only red parts
    #red_balloons = cv2.bitwise_and(frame, frame, mask=mask_total)

    # Find contours in the masked image (potential balloons)
    contours, _ = cv2.findContours(mask_total, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        if area < 1 or area > 400:
            continue 

        approx_contour = cv2.approxPolyDP(contour, epsilon=0.1 * perimeter, closed=True)

        # Bounding box to check aspect ratio
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = float(w) / h

        if((w > 0.6*area) or (h > 0.6*area)):
            continue
        
        # Check shape similarity to a circle
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        approx_vertices = len(approx_contour)

        circularity = (4 * np.pi * area) / (perimeter ** 2) if perimeter > 0 else 0

        if 0.8 < aspect_ratio < 1.2 and 0.75 < circularity < 1.2:  
            print(f"Red balloon detected. ({x}, {y})")
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.drawContours(frame, [approx_contour], 0, (0, 255, 0), 3)

        
        # Draw the contour if it's a potential balloon
        if approx_contour is not None:
            cv2.drawContours(frame, [approx_contour], 0, (0, 255, 0), 3)

    # Display the frame with detected red balloons
    cv2.imshow('Red Balloons', frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources and close windows
cap.release()
cv2.destroyAllWindows()
