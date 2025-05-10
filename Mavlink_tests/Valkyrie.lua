---@diagnostic disable
-- https://mavlink.io/en/messages/ardupilotmega.html

-- keep this at the top of your script:
local recorded_coords = {}
local COORD_TOL = 1e-5

-- helper: has this (lat,lon) already been recorded?
local function coord_exists(lat, lon)
  for _, p in ipairs(recorded_coords) do
    if math.abs(p.lat - lat) < COORD_TOL
       and math.abs(p.lon - lon) < COORD_TOL then
      return true
    end
  end
  return false
end

-- your regular update() function, running once per second:
local function update()
  gcs:send_text(6, "STAT:0.00;ALT:0.00;POS:0.00,0.00")
    
  -- 1) read vehicle ground speed
  if not ahrs:get_velocity_NED() then
    gcs:send_text(6, "STAT:0.00;ALT:0.00;POS:0.00,0.00")
    return update, 1000
  end
  local speed = ahrs:get_velocity_NED():length()

  -- 2) if effectively stopped, grab GPS + altitude and record
  if speed <= 0.5 then
    local gps = gps:location(0)  -- Fetch the first GPS device's location
    if gps then
      local lat = gps:lat() / 1e7  -- Convert from 1e7 to normal degrees
      local lon = gps:lng() / 1e7  -- Convert from 1e7 to normal degrees
      -- read altitude from barometer (in metres)
      local alt = baro:get_altitude() or 0

      if not coord_exists(lat, lon) then
        -- log to GCS
        gcs:send_text(6, string.format("STAT:1;ALT:%.1f;POS:%.10f,%.10f", alt, lat, lon))
        -- store it
        table.insert(recorded_coords, {
          lat = lat,
          lon = lon,
          alt = alt
        })
      else
        gcs:send_text(6, "STAT:0.00;ALT:0.00;POS:0.00,0.00")
      end
    else
      gcs:send_text(6, "STAT:0.00;ALT:0.00;POS:0.00,0.00")
    end
  else
    gcs:send_text(6, "STAT:0.00;ALT:0.00.00;POS:0.00,0.00")
  end

  if baro:get_altitude() > 23 then
    while true do
      gcs:send_text(6, "STAT:X;ALT:0.00;POS:0.00,0.00")
    end

  end

  -- …any other periodic work here…

  -- schedule next call in 1000 ms
  return update, 1000
end

-- launch the loop
return update()