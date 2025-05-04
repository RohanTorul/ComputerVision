import numpy as np
from detect_ir import HotspotDetector
from pyproj import Transformer
import cv2
from mpi import MissionPlannerInterface
import time

mpi_instance = MissionPlannerInterface(port=5760)  # Initialize the Mission Planner Interface
while True:
    print(mpi_instance.get_data('STAT'))
    print("one loop done")
    time.sleep(0.1)  # Sleep for a second to avoid flooding the socket with requests
