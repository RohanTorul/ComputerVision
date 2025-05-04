local Publisher = require("Publisher")
local pub = Publisher:new(5760, {["STAT"]=nil,["POS"]=nil, ["ALT"]=nil}) -- whatever we need
function pub:update_attributes()
    random_number = math.random()
    if random_number < 0.45 then
        pub.attributes["STAT"] = 0
    elseif random_number < 0.9 then
        pub.attributes["STAT"] = 1
    else
        pub.attributes["STAT"] = -1
    end
    pub.attributes["POS"] = string.format("%f,%f",math.random()+50,math.random()+110)
    pub.attributes["ALT"] = math.random(20,25) -- random altitude
end
while true do
    pub:update_attributes()
    pub:step()
    socket.sleep(0.1)  -- send every 0.1 second
end