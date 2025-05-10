import cv2
import numpy as np
from detect_ir import HotspotDetector
import pickle 


def main():
    Ir_detector = HotspotDetector(camera_index=4)
    saved_frames = []
    while True:
        _,frame = Ir_detector.cap.read()
        if frame is not None:
            cv2.imshow("frame", frame)
        else:
            print("No frame")
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if cv2.waitKey(1) & 0xFF == 32:
            saved_frames.append(frame)
            print("frame saved: ", len(saved_frames))
        

    data = {"frames": saved_frames}
    print(len(saved_frames))
    with open("frames.pkl", "wb") as f:
        pickle.dump(data, f)

main()





