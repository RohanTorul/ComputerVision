-- publisher.lua
local socket = require("socket")
local server = assert(socket.bind("*", 12345))
server:settimeout(0)  -- non-blocking server

print("Lua TCP publisher running on port 12345...")

local clients = {}

-- Simulate attribute:value data generation
local function generate_data()
    return "speed:34,temp:76,time:" .. os.time() .. "\n"
end

while true do
    -- Accept new clients
    local client = server:accept()
    if client then
        client:settimeout(0)  -- non-blocking client
        table.insert(clients, client)
        print("Client connected.")
    end

    -- Broadcast data to all connected clients
    local data = generate_data()
    for i = #clients, 1, -1 do
        local c = clients[i]
        local success, err = c:send(data)
        if not success then
            print("Client disconnected:", err)
            c:close()
            table.remove(clients, i)
        end
    end

    socket.sleep(0.2)  -- send every 1 second
end
