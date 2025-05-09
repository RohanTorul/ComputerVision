from detect_ir import HotspotDetector
import cv2
import time
def main():
    detector = HotspotDetector(camera_index=4)
    while True:
        ret, frame = detector.cap.read()
        processed_frames = []
        processed_contours = []
        if not ret:
            print("No frame captured.")
            continue
        if detector.validate_frame(frame): 
            print("Valid frame.")
            for contrast_threshold in range(0,40,5):
                f,c,_ = detector.detect_hotspots(frame, min_area=1,max_area=100,intensity_percentile=99.9 ,contrast_threshold=contrast_threshold,circularity_threshold=0.8)
                if c is None or len(c) == 0:
                    continue
                else:
                    processed_frames.append(f)
                    processed_contours.append(c) 

            #print(len(contours), " hotspots found.")
            if len(processed_contours) == 0:
                print("No hotspots found.")

            else:
                print(len(processed_contours[-1]), " hotspots found.")
                for cont in processed_contours[-1]:
                    cv2.drawContours(frame, cont, -1, (255, 0, 0), 2)
                    cv2.putText(frame,f"{cv2.contourArea(cont):.2f}", (cont[0][0][0], cont[0][0][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2 )
                    cv2.putText(processed_frames[-1],f"{cv2.contourArea(cont):.2f}", (cont[0][0][0], cont[0][0][1]), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2 )

        else:
            #print("Invalid frame.")
            pass
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        
        cv2.imshow("IR Simulation", frame)
        if len(processed_frames) == 0:
            cv2.imshow("Processed Frames(nothing found)", frame)
        else: cv2.imshow("Processed Frames", processed_frames[-1])


if __name__ == "__main__":
    main()
