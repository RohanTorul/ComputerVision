local socket = require("socket")
local Publisher = {}
Publisher.__index = Publisher

function Publisher:new(port, attributes)
    local self = setmetatable({}, Publisher)
    self.port = port or 12345
    self.server = assert(socket.bind("*", self.port))
    self.server:settimeout(0)
    self.clients = {}
    self.attributes = attributes
    print("Lua TCP publisher running on port " .. self.port .. "...")
end

function Publisher:update_attributes()
    --TODO:implement
end

function Publisher:generate_data() -- format: "key1;value1,key2;value2,...\n"
    local message = ""
    for k, v in pairs(self.attributes) do
        message = message .. k .. ";" .. tostring(v) .. ";" 
    end
    message = message .. "\n"  -- add \n
    return message
end
function Publisher:step()
    local client = self.server:accept()
    if client then
        client:settimeout(0)  -- non-blocking client
        table.insert(self.clients, client)
        print("Client connected.")
    end

    -- Broadcast data to all connected clients
    --self:update_attributes()  -- update attributes before sending CALLED MANUALLY NOW
    local data = self:generate_data()


    for i = #self.clients, 1, -1 do
        local c = self.clients[i]
        local success, err = c:send(data)
        if not success then
            print("Client disconnected:", err)
            c:close()
            table.remove(self.clients, i)
        end
    end
end

function Publisher:run()
    while true do
        self:step()
        socket.sleep(0.1)  -- send every 0.2 second
    end
end