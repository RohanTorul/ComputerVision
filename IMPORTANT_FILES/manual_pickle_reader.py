import pickle
import cv2
from Finder import CoordinateTransformer
import argparse
import numpy as np
from detect_ir import HotspotDetector
from Finder import UAV_GROUND_PERCEPTION
import simplekml

FOV = 60
def get_alt_pos_array(alt_pos_file):
    result = []
    with open(alt_pos_file, 'r') as file:
        for line in file:
            stripped = line.strip()
            if not stripped:
                continue  # skip empty lines
            parts = stripped.split(',')
            if len(parts) != 3:
                raise ValueError(f"Invalid line: {line}")
            lat, lon, alt = map(float, parts)
            result.append((alt, (lat, lon)))
    return result
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        f,alt,pos = param
        X_dimension, Y_dimension, _ = f.shape
        chunk_length_half = float(alt)* np.tan(np.radians(FOV/2)) # TODO: check if this is correct#
        coordinate_transformer = CoordinateTransformer()
        coordinate_transformer.init_transformer(pos[0], pos[1])
        x_distance = (x - X_dimension / 2) * chunk_length_half / X_dimension
        y_distance = (y - Y_dimension / 2) * chunk_length_half / Y_dimension
        lon, lat = coordinate_transformer.inverse_transformer.transform(x_distance, y_distance)
        print(f"Clicked coordinates: x={x}, y={y}")
        print(f"Clicked coordinates: lon={lon}, lat={lat}")
if __name__ == '__main__':
    argparder = argparse.ArgumentParser("You need to provide pickle file, and alt pos file")
    argparder.add_argument("pickle_file", type=str, help="pickle file path")
    argparder.add_argument("alt_pos_file", type=str, help="alt pos file path")
    args = argparder.parse_args()
    with open(args.pickle_file, "rb") as f:
        data = pickle.load(f)
    alt_pos_array = get_alt_pos_array(args.alt_pos_file)
    alt_pos_index = 0
    detected_hotspots = set()
    new_hotspots_location = set()
    fire_source_coordinates: tuple = (0, 0) # FORMAT: (LONGITUDE, LATITUDE)
    source_description = "fire source"
    Finder = UAV_GROUND_PERCEPTION(source_description = source_description, Source_of_fire_coordinate = fire_source_coordinates,fov=FOV)

    kml = simplekml.Kml()
    firesource_point = kml.newpoint(name="source", coords = [fire_source_coordinates])
    firesource_point.description = source_description
    kml.save("Task1.kml")

    frames = data["frames"]
    for frame in frames:
        new_hotspots_location= set()

        current_hotspot_count = len(detected_hotspots)

        alt, pos = alt_pos_array[alt_pos_index]
        new_hotspots_location= Finder.process_single_frame((frame.copy(), alt, pos))

        if len(new_hotspots_location) > 0:

            for hotspot in new_hotspots_location:
                detected_hotspots.add(hotspot)
                if len(detected_hotspots) > current_hotspot_count:
                    current_hotspot_count = len(detected_hotspots)
                    hotspot_point = kml.newpoint(name=f"Hotspot {current_hotspot_count}", coords = [hotspot[1],hotspot[0]])
                    hotspot_point.altitudemode = simplekml.AltitudeMode.relativetoground
                    kml.save("Task1.kml")

        alt_pos_index  = (alt_pos_index + 1) % len(alt_pos_array)
    
    frame_index = 0
    alt_pos_index = 0
    try:
        while True:
            alt, pos = alt_pos_array[alt_pos_index]
            frame = frames[frame_index]
            cv2.imshow("frame", frame)
            cv2.setMouseCallback("frame", mouse_callback(alt, pos))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if cv2.waitKey(1) & 0xFF == 32:
                frame_index = (frame_index + 1) % len(frames)
                alt_pos_index = (alt_pos_index + 1) % len(alt_pos_array)

    except Exception:
        print("Error doing interactive mode")
        pass
            
        