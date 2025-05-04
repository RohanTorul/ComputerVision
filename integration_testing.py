import numpy as np
from detect_ir import HotspotDetector
from pyproj import Transformer
import cv2
from mpi import MissionPlannerInterface
import time
detect_ir_instance = HotspotDetector(camera_index=4)  # Initialize the Hotspot Detector
mpi_instance = MissionPlannerInterface(port=5760)  # Initialize the Mission Planner Interface
vision_output = []  # List to store vision output data

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




while True:
    stat = None
    altitude = None
    position = None
    current_message = mpi_instance.get_dict()
    if current_message is None:
        continue
    if 'STAT' in current_message:
        stat = current_message['STAT']
    else:
        continue
    if stat is None:
        #print("No data available yet.")
        continue
    status = int(stat)
    print(status)    
    if status == 0:
        print("UAV not on target")
       
    elif status == -1:
        print("UAV returning to base")
        break
        
    elif status == 1:
        print("UAV on target")
        if 'ALT' in current_message:
            altitude = current_message['ALT']
        else: continue
        if 'POS' in current_message:
            position = current_message['POS']
        else: continue
        if position is None or altitude is None:
            print("was unable to get position or altitude")
            continue
        position = position.split(',')
        print("UAV on target")
        frame = detect_ir_instance.return_valid_frame()
        if frame is None:
            print("No valid frame available yet.")
            continue
        else:
            vision_output.append((frame,altitude,(float(position[0]),float(position[1]))))

frame_number = 0
#processed_frames = []
contours = []
for frame in vision_output:
    _,c,_ = detect_ir_instance.detect_hotspots(frame[0])
    
    contours.append(c)

while True:
    frame_number = (frame_number + 1)
    if frame_number == len(vision_output):
        break
    # Process the vision output
    cv2.drawContours(vision_output[frame_number][0], contours[frame_number], -1, (0, 0, 255), 2)
    # Check for exit condition (e.g., key press)
    cv2.imshow(f"Vision Output {vision_output[frame_number][1]},{vision_output[frame_number][2]}", vision_output[frame_number][0])

hotspot_locations= []
fov = 30
for frame, alt, pos in vision_output:
    p, c, t = detect_ir_instance.detect_hotspots(frame)
    X_dimension, Y_dimension, _ = frame.shape
    for contour in c:
        x, y, w, h = cv2.boundingRect(contour)
        chunk_length_half = float(alt)* np.tan(np.radians(fov/2)) # TODO: check if this is correct#

        coordinate_transformer = CoordinateTransformer()
        coordinate_transformer.init_transformer(pos[0], pos[1])
        x_distance = (x - X_dimension / 2) * chunk_length_half / X_dimension
        y_distance = (y - Y_dimension / 2) * chunk_length_half / Y_dimension
        lon, lat = coordinate_transformer.inverse_transformer.transform(x_distance, y_distance)
        hotspot_locations.append((lat, lon))

print(hotspot_locations)

while True:

    if cv2.waitKey(1) & 0xFF == ord('q'):
        cv2.destroyAllWindows()
        break
   





    '''
    # TEST 1 SUCCESSFUL
    stat = mpi_instance.get_data('STAT')
    if stat is not None:
        print(f"STAT: {stat}")  # Print the STAT data for debugging
    else:
        continue
        #print("No STAT data available yet.")
    #print("one loop done")
    #time.sleep()  # Sleep for a second to avoid flooding the socket with requests
    '''