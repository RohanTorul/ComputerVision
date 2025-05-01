import numpy as np
from detect_ir import detect_hotspots

from pyproj import Transformer

class PathGenerator:
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
        Generate a snake-like path relative to the target position and return GPS waypoints.
        target_position: (latitude, longitude)
        Returns: list of (lat, lon) tuples
        """
        lat0, lon0 = target_position
        self.init_transformer(lat0, lon0)

        # Example snake-like path in meters, relative to the target (0,0)
       

        path_gps = []
        for x, y in path_relative:
            lon, lat = self.inverse_transformer.transform(x, y)
            path_gps.append((lat, lon))

        return path_gps


class UAV_GROUND_PERCEPTION:
    def __init__(chunk_size = self,radius = 100,position = (0,0),initial_target = (0,0)):
        #self.map = np.zeros((self.WIDTH,self.HEIGHT,1), dtype=np.uint8)# map of the restricted airspace discretized in chuncks (x,y,IsRelevant)
        #self.visited_chunks = set()
        #self.chunk_size = chunk_size
        #.surrounding_chunks = []
        #self.targets = {hotspots:[], balloons:initial_target}
        self.search_radius = radius # search radius for the UAV to search for targets
        self.position = position
        self.vison_output = []
        self.alpha = 0.
        self.path_state = 0
        self.path = self.generate_path(initial_target)
        self.current_active_target = self.path[0]
        self.Bounds = [] # TODO: define the bounds of the search area

        
    def Is_OOB():
        pass
    def generate_path(self, target_position):
        path_gen = PathGenerator()
        path_relative = [
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
        ]
        path = path_gen.generate_path(target_position, path_relative)
        return path
    
    def CV_GetVisionOutput(self):
        # This function should return the vision output from the camera, like the whole unprocessed image. processing is done hereby ir_detector.py class
        return None

    def update(self):

        if self.path_state < len(self.path):
            if self.position == self.current_active_target:
                self.vision_output.append(self.CV_GetVisionOutput())
                self.path_state += 1
                if self.path_state < len(self.path):
                    self.current_active_target = self.path[self.path_state]
                    return 0
            else:
                if self.path_state < len(self.path):
                    self.current_active_target = self.path[self.path_state]
        else:
            return -1  # Path completed

def main():
    """
    Main function to run the UAV_GROUND_PERCEPTION class.
    """
    # Initialize the UAV_GROUND_PERCEPTION class
    uav_perception = UAV_GROUND_PERCEPTION(chunk_size=10, Width=640, Height=480, position=(0, 0), initial_target=(0, 0))

    # Update the UAV perception system
    uav_perception.update()

    # Print the current position and vision output
    print("Current Position:", uav_perception.position)
    print("Vision Output:", uav_perception.vision_output)
if __name__ == "__main__":
    main()

