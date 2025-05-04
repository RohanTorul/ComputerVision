local Publisher = require("Publisher")
local pub = Publisher:new(5760, {["STAT"]=nil,["POS"]=nil, ["ALT"]=nil}) -- whatever we need
function pub:update_attributes()
    pub.attributes["STAT"] = math.random(0, 1) -- random status
    pub.attributes["POS"] = math.random(0, 100) -- random position
    pub.attributes["ALT"] = math.random(0, 100) -- random altitude
end
while true do
    pub:update_attributes()
    pub:step()
    socket.sleep(0.1)  -- send every 0.1 second
end