import pickle
import cv2
from Finder import CoordinateTransformer
import argparse
import numpy as np

def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            alt, pos = param
            chunk_length_half = float(alt) * np.tan(np.radians(60 / 2))  # TODO: check if this is correct#
            coordinate_transformer = CoordinateTransformer()
            coordinate_transformer.init_transformer(pos[0], pos[1])
            x_distance = (x - 640 / 2) * chunk_length_half / 640
            y_distance = (y - 480 / 2) * chunk_length_half / 480
            lon, lat = coordinate_transformer.inverse_transformer.transform(x_distance, y_distance)
            print(f"Clicked coordinates: x={x}, y={y}")
            print(f"Clicked coordinates: lon={lon}, lat={lat}")




parser = argparse.ArgumentParser("path to pickle file")
parser.add_argument("file", help="path to pickle file")
args = parser.parse_args()



data = None
if args.file:
    with open(args.file, 'rb') as f:
        data = pickle.load(f)
        f.close()
if data:

    vision_output = data.get('vision_output')
    potentially_invalid_frames = data.get('potentially_invalid_frames')
    vision_index = 0
    if vision_output is not None and len(vision_output) > 0:
        while True:
            frame, alt, pos = vision_output[vision_index]
            cv2.imshow('valid_frame', frame)
            cv2.setMouseCallback('valid_frame', mouse_callback, (alt, pos))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if cv2.waitKey(1) & 0xFF == 32:# space
                vision_index = (vision_index + 1) % len(vision_output)
                print("now showing frame ", vision_index)
    else: print("No valid frames")

    invalid_index = 0
    if potentially_invalid_frames is not None and len(potentially_invalid_frames) > 0:
        while True:
            frame, alt, pos = potentially_invalid_frames[invalid_index]
            cv2.imshow('invalid_frame', frame)
            cv2.setMouseCallback('invalid_frame', mouse_callback, (alt, pos))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if cv2.waitKey(1) & 0xFF == 32:# space
                invalid_index = (invalid_index + 1) % len(potentially_invalid_frames)
                print("now showing frame ", invalid_index)
    else: print("No invalid frames")