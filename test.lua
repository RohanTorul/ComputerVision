---@diagnostic disable
-- https://mavlink.io/en/messages/ardupilotmega.htmL


-- publisher.lua
local socket = require("socket")
local server = assert(socket.bind("*", 12345))
server:settimeout(0)  -- non-blocking server

print("Lua TCP publisher running on port 12345...")

local clients = {}
local attributes = {position=nil, altitude=nil, targetPosition=nil} -- whatever we need
-- Simulate attribute:value data generation
local function update_attributes()
    --TODO:implement
end
local function generate_data()
    local messager = ""
    for k, v in pairs(attributes) do
        messager = messager .. k .. ":" .. tostring(v) .. "," 
    end
    messager = messager .. "\n"  -- add \n
    return messager
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
