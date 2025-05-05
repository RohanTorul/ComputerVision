local CHECK_INTERVAL = 100 -- 0.1 second between checks
local HOVER_THRESHOLD = 0.5 -- m/s velocity considered as hovering

function get_velocity()
    local vel = ahrs:get_velocity_NED()
    if not vel then return 0 end
    return vel:length()
end

function is_hovering()
    return get_velocity() < HOVER_THRESHOLD and baro:get_altitude() > 5.0
end

function is_returning_home()
    return vehicle:get_mode() == "RTL" -- Assumes ArduPilot mode names
end

function send_status(hover_state)
    local myalt = baro:get_altitude()
    local mypos = ahrs:get_position()
    
    if hover_state == 1 then
        gcs:send_text(2, string.format("STAT:1;ALT:%.6f;POS:%.1f,%.1f\n", 
                      -myalt, mypos:lat(), mypos:lng()))
    elseif hover_state == 2 then
        gcs:send_text(2, "STAT:X;ALT:0.00;POS:0.0,0.0\n")
    else
        gcs:send_text(2, "STAT:0;ALT:0.00;POS:0.0,0.0\n")
    end
end

function update()
    if not arming:is_armed() then
        if not arming:arm() then
            return update, CHECK_INTERVAL
        end
    end
    if is_returning_home() then
        send_status(2)
    elseif is_hovering() then
        send_status(1)
    else
        send_status(0)
    end
    return update, CHECK_INTERVAL
end

return update()