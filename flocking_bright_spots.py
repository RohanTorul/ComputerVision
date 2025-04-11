import numpy as np
import cv2
import random
import math

class FlockingSpots:
    def __init__(self, width=800, height=600, num_spots=30):
        self.width = width
        self.height = height
        self.num_spots = num_spots
        self.spots = []
        self.target_pos = None
        self.cluster_rect = None
        self.grid_size = 50
        self.uav_pos = (self.width//4, self.height//4)  # UAV position (x,y)
        self.uav_altitude = 100  # UAV altitude in pixels
        self.uav_heading = 0  # UAV heading angle in degrees (0 = right, 90 = up)
        self.uav_size = 15  # Size of UAV marker
        self.initialize_spots()
        
    def initialize_spots(self):
        """Create initial random spots"""
        for _ in range(self.num_spots):
            x = random.randint(20, self.width - 20)
            y = random.randint(20, self.height - 20)
            radius = random.randint(5, 10)
            speed_x = random.uniform(-1, 1)
            speed_y = random.uniform(-1, 1)
            self.spots.append({
                'x': x, 'y': y, 
                'radius': radius,
                'speed_x': speed_x, 
                'speed_y': speed_y,
                'brightness': random.randint(200, 255),
                'max_speed': random.uniform(1.0, 2.0)
            })
    
    def set_target(self, x, y):
        """Set a new target position for the flock"""
        self.target_pos = (x, y)
    
    def calculate_uav_metrics(self):
        """Calculate all UAV-related metrics"""
        if not self.cluster_rect:
            return None, None, None
            
        # Get cluster center
        x1, y1, x2, y2 = self.cluster_rect
        cluster_center = ((x1 + x2)/2, (y1 + y2)/2)
        
        # Calculate ground distance (2D distance)
        dx = self.uav_pos[0] - cluster_center[0]
        dy = self.uav_pos[1] - cluster_center[1]
        ground_distance = math.sqrt(dx**2 + dy**2)
        
        # Calculate 3D distance (including altitude)
        distance_3d = math.sqrt(ground_distance**2 + self.uav_altitude**2)
        
        # Calculate angle of elevation (in degrees)
        angle_rad = math.atan2(self.uav_altitude, ground_distance)
        angle_deg = math.degrees(angle_rad)
        
        # Calculate bearing to target (0-360 degrees, 0 = right, 90 = up)
        bearing = math.degrees(math.atan2(cluster_center[1] - self.uav_pos[1], 
                                      cluster_center[0] - self.uav_pos[0]))
        bearing = (bearing + 360) % 360  # Normalize to 0-360
        
        # Calculate relative angle between UAV heading and target
        relative_angle = (bearing - self.uav_heading + 360) % 360
        if relative_angle > 180:
            relative_angle -= 360  # Shows left/right more intuitively
        
        return angle_deg, distance_3d, relative_angle
    
    def find_dense_cluster(self):
        """Find the densest group of spots and return its bounding rectangle"""
        if len(self.spots) < 3:
            return None
            
        max_count = 0
        best_center = None
        
        for spot in self.spots:
            center_x, center_y = spot['x'], spot['y']
            count = 0
            
            for other in self.spots:
                dist = math.sqrt((other['x'] - center_x)**2 + (other['y'] - center_y)**2)
                if dist < 100:
                    count += 1
            
            if count > max_count:
                max_count = count
                best_center = (center_x, center_y)
        
        if max_count < 3:
            return None
            
        min_x, max_x = float('inf'), 0
        min_y, max_y = float('inf'), 0
        
        for spot in self.spots:
            dist = math.sqrt((spot['x'] - best_center[0])**2 + (spot['y'] - best_center[1])**2)
            if dist < 100:
                min_x = min(min_x, spot['x'])
                max_x = max(max_x, spot['x'])
                min_y = min(min_y, spot['y'])
                max_y = max(max_y, spot['y'])
        
        padding = 20
        return (
            max(0, min_x - padding),
            max(0, min_y - padding),
            min(self.width, max_x + padding),
            min(self.height, max_y + padding)
        )
    
    def update_spots(self):
        """Update spot positions with flocking behavior"""
        if self.target_pos:
            target_x, target_y = self.target_pos
            
        for spot in self.spots:
            if self.target_pos:
                dx = target_x - spot['x']
                dy = target_y - spot['y']
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance < 5:
                    spot['speed_x'] *= 0.9
                    spot['speed_y'] *= 0.9
                    continue
                    
                if distance > 0:
                    dx /= distance
                    dy /= distance
            
            separation = self.calculate_separation(spot)
            alignment = self.calculate_alignment(spot)
            cohesion = self.calculate_cohesion(spot)
            
            spot['speed_x'] += (dx * 0.05 if self.target_pos else 0) + separation[0] * 0.1 + alignment[0] * 0.05 + cohesion[0] * 0.03
            spot['speed_y'] += (dy * 0.05 if self.target_pos else 0) + separation[1] * 0.1 + alignment[1] * 0.05 + cohesion[1] * 0.03
            
            speed = math.sqrt(spot['speed_x']**2 + spot['speed_y']**2)
            if speed > spot['max_speed']:
                spot['speed_x'] = (spot['speed_x'] / speed) * spot['max_speed']
                spot['speed_y'] = (spot['speed_y'] / speed) * spot['max_speed']
            
            spot['x'] += spot['speed_x']
            spot['y'] += spot['speed_y']
            
            spot['x'] = np.clip(spot['x'], spot['radius'], self.width - spot['radius'])
            spot['y'] = np.clip(spot['y'], spot['radius'], self.height - spot['radius'])
        
        self.cluster_rect = self.find_dense_cluster()
    
    def calculate_separation(self, spot):
        separation_x, separation_y = 0, 0
        neighbors = 0
        separation_distance = 30
        
        for other in self.spots:
            if other == spot:
                continue
                
            dx = spot['x'] - other['x']
            dy = spot['y'] - other['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < separation_distance:
                if distance > 0:
                    separation_x += dx / distance
                    separation_y += dy / distance
                neighbors += 1
        
        if neighbors > 0:
            separation_x /= neighbors
            separation_y /= neighbors
            
        return separation_x, separation_y
    
    def calculate_alignment(self, spot):
        avg_x, avg_y = 0, 0
        neighbors = 0
        neighbor_distance = 80
        
        for other in self.spots:
            if other == spot:
                continue
                
            dx = spot['x'] - other['x']
            dy = spot['y'] - other['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < neighbor_distance:
                avg_x += other['speed_x']
                avg_y += other['speed_y']
                neighbors += 1
        
        if neighbors > 0:
            avg_x /= neighbors
            avg_y /= neighbors
            
        return avg_x, avg_y
    
    def calculate_cohesion(self, spot):
        center_x, center_y = 0, 0
        neighbors = 0
        neighbor_distance = 100
        
        for other in self.spots:
            if other == spot:
                continue
                
            dx = spot['x'] - other['x']
            dy = spot['y'] - other['y']
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < neighbor_distance:
                center_x += other['x']
                center_y += other['y']
                neighbors += 1
        
        if neighbors > 0:
            center_x /= neighbors
            center_y /= neighbors
            return (center_x - spot['x']) * 0.01, (center_y - spot['y']) * 0.01
        return 0, 0
    
    def draw_grid(self, img):
        color = (150, 150, 150)
        
        for x in range(0, self.width, self.grid_size):
            cv2.line(img, (x, 0), (x, self.height), color, 1)
        
        for y in range(0, self.height, self.grid_size):
            cv2.line(img, (0, y), (self.width, y), color, 1)
        
        return img
    
    def draw_uav(self, img):
        """Draw the UAV with orientation and altitude"""
        # Calculate UAV top position (at altitude)
        uav_top = (self.uav_pos[0], self.uav_pos[1] - self.uav_altitude)
        
        # Draw altitude line
        cv2.line(img, self.uav_pos, uav_top, (100, 100, 255), 2)
        
        # Draw UAV ground position
        cv2.circle(img, (int(self.uav_pos[0]), int(self.uav_pos[1])), 8, (255, 0, 0), -1)
        
        # Draw UAV body at altitude
        cv2.circle(img, (int(uav_top[0]), int(uav_top[1])), self.uav_size//2, (0, 0, 255), -1)
        
        # Calculate front direction vector
        angle_rad = math.radians(self.uav_heading)
        front_length = self.uav_size * 1.5
        front_x = uav_top[0] + front_length * math.cos(angle_rad)
        front_y = uav_top[1] + front_length * math.sin(angle_rad)
        
        # Draw heading indicator
        cv2.line(img, (int(uav_top[0]), int(uav_top[1])), 
                (int(front_x), int(front_y)), (0, 255, 255), 2)
        
        return img
    
    def draw_spots(self):
        img = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        img = self.draw_grid(img)
        img = self.draw_uav(img)
        
        if self.target_pos:
            target_x, target_y = self.target_pos
            cv2.circle(img, (int(target_x), int(target_y)), 10, (0, 0, 255), 2)
            cv2.circle(img, (int(target_x), int(target_y)), 3, (0, 0, 255), -1)
        
        for spot in self.spots:
            if self.target_pos:
                target_x, target_y = self.target_pos
                distance = math.sqrt((spot['x'] - target_x)**2 + (spot['y'] - target_y)**2)
                max_distance = math.sqrt(self.width**2 + self.height**2)
                intensity = int(255 * (1 - distance/max_distance))
                color = (intensity, intensity, spot['brightness'])
            else:
                color = (spot['brightness'], spot['brightness'], spot['brightness'])
            
            cv2.circle(img, (int(spot['x']), int(spot['y'])), 
                       spot['radius'], color, -1)
        
        if self.cluster_rect:
            x1, y1, x2, y2 = self.cluster_rect
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # Calculate and display UAV metrics
            angle, distance, rel_angle = self.calculate_uav_metrics()
            if angle is not None:
                cluster_center = ((x1 + x2)/2, (y1 + y2)/2)
                
                # Draw line from UAV to cluster center
                uav_top = (self.uav_pos[0], self.uav_pos[1] - self.uav_altitude)
                cv2.line(img, (int(uav_top[0]), int(uav_top[1])),
                        (int(cluster_center[0]), int(cluster_center[1])),
                        (255, 255, 0), 2)
                
                # Display metrics
                cv2.putText(img, f"Elevation: {angle:.1f}deg", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(img, f"Distance: {distance:.1f}px", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(img, f"Bearing: {rel_angle:.1f}deg from UAV heading", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(img, f"UAV Heading: {self.uav_heading:.1f}deg", 
                           (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.putText(img, "WASD:Move | QE:Rotate | +/-:Altitude | Click:MoveFlock | R:Reset", 
                   (10, self.height-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return img

def main():
    flock = FlockingSpots(width=800, height=600, num_spots=30)
    window_name = "UAV Flock Monitoring with Rotation"
    cv2.namedWindow(window_name)
    
    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            flock.set_target(x, y)
    
    cv2.setMouseCallback(window_name, mouse_callback)
    
    while True:
        flock.update_spots()
        frame = flock.draw_spots()
        cv2.imshow(window_name, frame)
        
        key = cv2.waitKey(30)
        if key == 27:  # ESC
            break
        elif key == ord('r'):
            flock = FlockingSpots(width=800, height=600, num_spots=30)
        elif key == ord('+'):
            flock.uav_altitude = min(300, flock.uav_altitude + 10)
        elif key == ord('-'):
            flock.uav_altitude = max(10, flock.uav_altitude - 10)
        elif key == ord('w'):
            flock.uav_pos = (flock.uav_pos[0], flock.uav_pos[1] - 10)
        elif key == ord('s'):
            flock.uav_pos = (flock.uav_pos[0], flock.uav_pos[1] + 10)
        elif key == ord('a'):
            flock.uav_pos = (flock.uav_pos[0] - 10, flock.uav_pos[1])
        elif key == ord('d'):
            flock.uav_pos = (flock.uav_pos[0] + 10, flock.uav_pos[1])
        elif key == ord('q'):  # Rotate counter-clockwise
            flock.uav_heading = (flock.uav_heading - 5) % 360
        elif key == ord('e'):  # Rotate clockwise
            flock.uav_heading = (flock.uav_heading + 5) % 360
    
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()