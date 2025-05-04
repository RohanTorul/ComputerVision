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
