import cv2
import numpy as np
import random
import time

def generate_random_image(width=1080, height=720, num_circles=10):
    # Create an empty image
    image = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Generate a mixed green and brown background to simulate grass and dirt
    for y in range(height):
        for x in range(width):
            if random.random() < 0.5:
                image[y, x] = (34, 139, 34)  # Green (grass)
            else:
                image[y, x] = (31, 43, 61)  # Brown (dirt)
    
    # Draw randomly distributed red circles
    for _ in range(num_circles):
        center = (random.randint(0, width-1), random.randint(0, height-1))
        radius = random.randint(5,10)
        color = (0, 0, random.randint(100,220))  # Red in BGR format
        cv2.circle(image, center, radius, color, -1)
    
    return image

# Display the image at 60 FPS
cv2.namedWindow('Random Ground with Red Circles')
while True:
    start_time = time.time()
    image = generate_random_image()
    cv2.imshow('Random Ground with Red Circles', image)
    
    # Maintain 60 FPS
    elapsed_time = time.time() - start_time
    delay = max(1, int((1/60 - elapsed_time) * 1000))
    if cv2.waitKey(delay) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
