local Publisher = require("publisher")
local pub = Publisher:new(5760, {["STAT"]=nil,["POS"]=nil, ["ALT"]=nil}) -- whatever we need

while true do
    Publisher:step()
    
end