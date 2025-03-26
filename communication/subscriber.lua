local zmq = require("lzmq")
local context = zmq.context()
local socket = context:socket(zmq.SUB)  -- SUB = Subscriber mode
socket:connect("tcp://localhost:5555")  -- Connect to publisher

socket:set_subscribe("")  -- Subscribe to all messages

while true do
    print("waiting...")
    local message = socket:recv()
    print("Received:", message)

    -- Parse the message (format: "DIRECTION VALUE")
    local direction, value = message:match("(%w+) (%d+)")
    
    if direction and value then
        print("Direction:", direction, " Value:", value)
        -- You can use these values to control something in Lua
    end
end
