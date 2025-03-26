local socket = require("socket")

-- Create a TCP connection to the Python server
local client = socket.connect("localhost", 5555)

-- Receive data from the server
local response, err = client:receive('*a')
if not err then
    print("Received from Python:", response)
else
    print("Error receiving data:", err)
end

-- Close the connection
client:close()
