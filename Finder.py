import numpy as np
from detect_ir import HotspotDetector
from pyproj import Transformer
import cv2
from mpi import MissionPlannerInterface
class CoordinateTransformer:
    def __init__(self):
        self.transformer = None
        self.inverse_transformer = None

    def init_transformer(self, lat0, lon0):
        """
        Initializes pyproj transformers for converting between local meters and GPS.
        """
        proj_string = f"+proj=tmerc +lat_0={lat0} +lon_0={lon0} +datum=WGS84"
        self.transformer = Transformer.from_crs("epsg:4326", proj_string, always_xy=True)
        self.inverse_transformer = Transformer.from_crs(proj_string, "epsg:4326", always_xy=True)

    def generate_path(self, target_position, path_relative = []):
        """
        target_position: (latitude, longitude)
        Returns: list of (lat, lon) tuples
        """
        lat0, lon0 = target_position
        self.init_transformer(lat0, lon0)

        path_gps = []
        for x, y in path_relative:
            lon, lat = self.inverse_transformer.transform(x, y)
            path_gps.append((lat, lon))

        return path_gps


class UAV_GROUND_PERCEPTION:
    def __init__(self,radius = 100,position = (0,0),initial_target = (0,0),fov = 60):
        self.search_radius = radius # search radius for the UAV to search for targets
        self.position = position
        self.altitude = 0. # altitude of the UAV
        self.vison_output = []
        self.alpha = 0.
        self.fov = fov # field of view of the camera
        self.path_state = 0
        self.path = self.generate_path(initial_target)
        self.current_active_target = self.path[0]
        self.Bounds = [] # TODO: define the bounds of the search area
        self.Ir_detector = HotspotDetector(camera_index= 4) #change cameraindex until it works ig.
        self.MPI = MissionPlannerInterface(port=5760) # TODO: define the mission planner interface

    def are_within_range(tuple1, tuple2, tolerance=0.0001):
        lat1, lon1 = tuple1
        lat2, lon2 = tuple2
    
        # Check if the absolute difference between latitudes and longitudes is within tolerance
        lat_diff = abs(lat1 - lat2)
        lon_diff = abs(lon1 - lon2)
    
        return lat_diff <= tolerance and lon_diff <= tolerance
    

    def Is_OOB():#TODO: define the function to check if a position is out of bounds
        pass
    def generate_path(self, target_position):
        path_gen = CoordinateTransformer()
        path_relative = np.array([
            (-self.search_radius, -self.search_radius), #TODO:hardcode this fing path.
            (5, 0),
            (5, 5),
            (0, 5),
            (-5, 5),
            (-5, 10),
            (0, 10),
            (5, 10),
            (5, 15),
            (0, 15),
        ])
        path = path_gen.generate_path(target_position, path_relative)
        return path
    
    def CV_GetVisionOutput(self):
        frame = self.Ir_detector.return_valid_frame()
        return frame
    
    def Mission_Planner_Get_Uav_Position(self):
        return self.MPI.get_data('GPS')  # Assuming 'GPS' is the key for position data
    
    # "STAT:1..;POS:(lat,lon);ALT:altitude;\n"

    def update(self):
        status = int(self.MPI.get_data('STAT'))
        if status == 0:
            print("UAV not on target")
            return -3
        elif status == -1:
            print("UAV returning to base")
            return -1
        elif status == 1:
            self.altitude = self.MPI.get_data('ALT')  # Assuming 'ALT' is the key for altitude data
            self.position = self.MPI.get_data('POS').split(",")  # Assuming 'POS' is the key for position data
            print("UAV on target")
            self.vision_output.append((self.CV_GetVisionOutput(),self.altitude,(float(self.position[0]),float(self.position[1]))))
            return 0

        
    def post_process(self):
        """
        Post-process the vision output to extract relevant information.
        """
        hotspot_locations= []

        for frame, alt, pos in self.vision_output:
            p, c, t = self.Ir_detector.detect_hotspots(frame)
            X_dimension, Y_dimension, _ = frame.shape
            for _,contour,_ in c:
                x, y, w, h = cv2.boundingRect(contour)
                chunk_length_half = alt* np.tan(np.radians(self.fov/2)) # TODO: check if this is correct#

                coordinate_transformer = CoordinateTransformer()
                coordinate_transformer.init_transformer(pos[0], pos[1])
                x_distance = (x - X_dimension / 2) * chunk_length_half / X_dimension
                y_distance = (y - Y_dimension / 2) * chunk_length_half / Y_dimension
                lon, lat = coordinate_transformer.inverse_transformer.transform(x_distance, y_distance)
                hotspot_locations.append((lat, lon))
        # Get frame dimensions

        return hotspot_locations

    
        
        # Label detected hotspots with their sector

def main():
    """
    Main function to run the UAV_GROUND_PERCEPTION class.
    """
    # Initialize the UAV_GROUND_PERCEPTION class
    uav_perception = UAV_GROUND_PERCEPTION(radius=100, position=(0, 0), initial_target=(0, 0), fov=60)

    # Update the UAV perception system
    while True:
        if uav_perception.update() == -1:
            print("UAV returning to base")
            break
        if uav_perception.update() == -3:
            print("UAV not on target")

    uav_perception.post_process()
    while True:
        # Process the vision output
        # Check for exit condition (e.g., key press)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Print the current position and vision output
    print("Current Position:", uav_perception.position)
    print("Vision Output:", uav_perception.vision_output)
if __name__ == "__main__":
    main()

