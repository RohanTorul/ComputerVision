# Instructions:
- activate venv, get the packages and whatnot
- run a simulation test script, there's goundtest and ir_groundtest currently.
- open OBS, record the window, then activate virtual camera
- open the detection script relevant for the test
- make sure you got the right camera selected(should be either 1 or 2 but could be anything really just keep incrementing from 0 until you get it)
- voila

- main.py or detect_ir.py ZMQ to send stream of sector information to Intermediary.py
- intermediary.py uses TCP sockets to communicate to Lua script(subscriber.lua)
- why? because.
# UPDATE 05/01/2025
- Main thing is in Finder.py
- depends on detect_it.py, mpi.py

# UPDATE 05/03/2025
- Finder.py
  - depends on
    - mpi.py
    - detect_ir.py
- main.lua
  - depends on
    - Publisher.lua

# UPDATE 05/04/2025
- Finder.py
  - Now uses mission_planner_file_interface.py
  - processes each frame instead of all at once.
  - control+F "SEE HERE" to see what I changed

 # UPDATE 05/08/2025
 - ALMOST DONE!
 - BEFORE RUNNING FINDER.PY:
  - Make sure you input the initial source coordinates you'll get on Mission Planner at the source of fire/Balloons
  - Make sure You are using the proper camera index.
  - When it is running, it will be in multiple loops.
    - first one is the Mavlink mission loop that will keep on going until it gets a STATX from Mission planner (PLEASE MAKE SURE YOU ARE RETURNING STATX)
    - Second one is a post processing one, you can use that for validation of the KML file.
    - Third one is a summary, displaying interactive images where you can click on the image and it will give you the corresponding lon lat coordinates.
      - enter key to cycle through Unvalidated frames
      - spacebar to cycle through validated frames
      - q to quit
# UPDATE 05/09/2025
- THIS IS IT FOLKS
- BEFORE RUNNING FINDER.PY:
  - connect camera and run analog_camera_test.py
    - move the camera around, see if it flags blatantly bad images. It's not perfect but eh.
    - if you want to tweak it, it is in detect_ir.py, look for validate_frame function. inside you can tweak the laplacian_thresh=,hist_spike_thresh= to whatever you need.
    - the lower the lapalcian_thresh or hist_spike_thresh, increases the chances of a frame being flagged as bad. Analog signals are noisy always so it's hard to tune.
  - Make sure you input the initial source coordinates you'll get on Mission Planner at the source of fire/Balloons
  - Make sure You are using the proper camera index.
    - inside Finder.py, lookup self.Ir_detector = HotspotDetector(camera_index= 4)
  - when you run it, there will be a live feed running on another thread. it will just show what the camera is giving. make sure to press q with the window in focus when you want to close it.
    - you will be asked to close it when all frames have processed. To display the processed frames and potentially invalid frames, you will need to press q.
  - When it is running, it will be in multiple sequential loops.
    - first one is the Mavlink mission loop that will keep on going until it gets a STATX from Mission planner (PLEASE MAKE SURE YOU ARE RETURNING STATX)
    - Second one is a post processing one, you can use that for validation of the KML file.
    - Third one is a summary, displaying interactive images where you can click on the image and it will give you the corresponding lon lat coordinates.
      - enter key to cycle through Unvalidated frames
      - spacebar to cycle through validated frames
      - q to quit
