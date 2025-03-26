local socket = require("socket")

while true do
    print("Attempting to connect to publisher...")
    local client = socket.connect("localhost", 6666)

    if client then
        print("Connected to publisher.")
        client:settimeout(nil)  -- Blocking mode (wait for message)

        while true do
            local message, err = client:receive(24)  -- Expecting exactly 24 characters
            
            if message then
                print("Received:", message)
            elseif err then
                print("Connection lost. Reconnecting...")
                break  -- Exit the loop to reconnect
            end
        end

        client:close()  -- Close connection before retrying
    else
        print("Failed to connect. Retrying in 3 seconds...")
        socket.sleep(3)  -- Prevents spamming connection attempts
    end
end
