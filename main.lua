---@diagnostic disable
-- https://mavlink.io/en/messages/ardupilotmega.htmL

local boundaries = {
  soft = {
    { lat=50.0971537, lon=-110.7329257 },
    { lat=50.1060519, lon=-110.7328869 },
    { lat=50.1060793, lon=-110.7436756 },
    { lat=50.1035452, lon=-110.7436555 },
    { lat=50.0989139, lon=-110.7381534 },
    { lat=50.0971788, lon=-110.7381487 },
    { lat=50.0971537, lon=-110.7329257 },  -- close the loop
  },

  hard = {
    { lat=50.0970884, lon=-110.7328077 },
    { lat=50.1061216, lon=-110.7327756 },
    { lat=50.1061482, lon=-110.7437887 },
    { lat=50.1035232, lon=-110.7437798 },
    { lat=50.0988785, lon=-110.7382540 },
    { lat=50.0971194, lon=-110.7382533 },
    { lat=50.0970884, lon=-110.7328077 },
  },
}

local MODE_GUIDED = 4
local MODE_ALTHOLD = 2
local MODE_LOITER = 5
local MODE_LAND = 9

local camera_angle = 29.79 -- degrees
local target_length = 25 -- meters

local target_alt = target_length/(2 * math.tan(camera_angle * math.pi/180)) -- 15m AGL at 29.79 degrees -> 17.28m altitude
local hover_duration = 10000   -- ms to hover
local descent_rate = 0.5       -- m/s during LAND

local stage = 0
local hover_start = 0
local initial_alt = nil

local survey_points     = nil
local survey_index      = 1
local survey_state      = 0
local survey_hover_start= 0
local start_lat, start_lon  -- set these in Stage 3

local goto_stage     = 0
local goto_start_ms  = 0
local target_loc     = nil

local function flyTo(lat, lon, alt_m)
  -- Stage 0: initialise
  
  if goto_stage == 0 then
    -- 1) build the Location
    target_loc = Location()
    target_loc:lat(math.floor(lat * 1e7))
    target_loc:lng(math.floor(lon * 1e7))
    target_loc:relative_alt(true)
    target_loc:alt(math.floor(alt_m * 100))

    -- 2) switch into GUIDED and send the waypoint
    vehicle:set_mode(MODE_GUIDED)
    vehicle:set_target_location(target_loc)
    gcs:send_text(6, string.format("Going to %.6f, %.6f @ %.1fm", lat, lon, alt_m))

    -- 3) start timer, advance sub‐state
    goto_start_ms = millis()
    goto_stage    = 1
    return false
  end

  -- Stage 1: waiting for arrival or timeout
  if goto_stage == 1 then
    local pos = ahrs:get_position()   -- nil until EKF+GPS ready
    if pos then
      local d = pos:get_distance(target_loc) or 999
      if d < 0.5 then
        gcs:send_text(6, "Arrived (dist="..string.format("%.2f",d).."m), hovering…")
        -- vehicle:set_mode(MODE_ALTHOLD)
        goto_stage = 2
        return true
      end
    end

    if millis() - goto_start_ms > 300000 then
      gcs:send_text(6, "Goto timeout, hovering anyway")
      -- vehicle:set_mode(MODE_ALTHOLD)
      goto_stage = 2
      return true
    end

    -- still en route
    return false
  end

  -- Stage 2: cleanup & allow a new waypoint
  if goto_stage == 2 then
    goto_stage     = 0
    goto_start_ms  = 0
    target_loc     = nil
    return true
  end
end

local function export_chunks_to_kml(filename)
  local fh, err = io.open(filename, "w")
  if not fh then
    gcs:send_text(6, "KML export failed: "..(err or "unknown error"))
    return
  end

  -- KML header
  fh:write('<?xml version="1.0" encoding="UTF-8"?>\n')
  fh:write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
  fh:write('  <Document>\n')
  fh:write('    <name>Survey Chunks</name>\n')
  fh:write('    <description>Automatically generated survey grid centers</description>\n')

  -- one Placemark per chunk
  for i, pt in ipairs(survey_points) do
    -- Note: KML uses lon,lat[,alt] order
    fh:write(string.format([[
    <Placemark>
      <name>Chunk %d</name>
      <Point>
        <coordinates>%.6f,%.6f,%.1f</coordinates>
      </Point>
    </Placemark>
]], i, pt.lon, pt.lat, target_alt))
  end

  -- close out
  fh:write('  </Document>\n')
  fh:write('</kml>\n')
  fh:close()

  gcs:send_text(6, "Exported KML to "..filename)
end

local function point_in_poly(lat, lon, poly)
  local inside = false
  for i = 1, #poly do
    local j = (i % #poly) + 1
    local yi, xi = poly[i].lat,  poly[i].lon
    local yj, xj = poly[j].lat,  poly[j].lon
    if ((yi > lat) ~= (yj > lat))
       and (lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) then
      inside = not inside
    end
  end
  return inside
end

local function survey_chunks_generator(start_lat, start_lon, soft_b, hard_b, cell_size, alt_m)
  local radius    = 100
  local half      = cell_size / 2
  local base_lat_i = math.floor(start_lat * 1e7)
  local base_lng_i = math.floor(start_lon * 1e7)
  local alt_cm     = math.floor(alt_m     * 100)

  -- cursors (in metres) and row counter
  local gn = -radius
  local row = 0
  -- we'll initialize ge when we enter each row
  local ge = nil

  return function()
    while gn <= radius - cell_size do
      -- start a new row if needed
      if ge == nil then
        if (row % 2) == 0 then
          -- even row: go west→east
          ge = -radius
        else
          -- odd  row: go east→west
          ge = radius - cell_size
        end
      end

      -- step through this row
      while (row % 2 == 0 and ge <= radius - cell_size)
         or (row % 2 == 1 and ge >= -radius) do

        local cn, ce = gn + half, ge + half
        -- advance ge for next time
        ge = ge + (row % 2 == 0 and cell_size or -cell_size)

        -- only check cells whose centre lies inside the circle
        if (cn*cn + ce*ce) <= (radius*radius) then
          -- build a Location at home → offset → back to degrees
          local loc = Location()
          loc:lat(      base_lat_i  )
          loc:lng(      base_lng_i  )
          loc:relative_alt(true)
          loc:alt(      alt_cm      )
          loc:offset(cn, ce)

          local lat = loc:lat() / 1e7
          local lon = loc:lng() / 1e7

          -- only return if inside both boundaries
          if point_in_poly(lat, lon, soft_b)
             and point_in_poly(lat, lon, hard_b) then
            return { lat = lat, lon = lon }
          end
        end
      end

      -- row done → advance to next
      ge = nil
      gn = gn + cell_size
      row = row + 1
    end

    -- completely exhausted
    return nil
  end
end

local function readyToArm()
    local gps_ok = gps:status(0)
    if not gps_ok then
        gcs:send_text(6, "Waiting for GPS 3D fix...")
        return false
    end

    local ekf_ok = (ahrs:get_position() ~= nil)
    if not ekf_ok then
        gcs:send_text(6, "Waiting for EKF position...")
        return false
    end

    local prearm_ok = ahrs:healthy()
    if not prearm_ok then
        gcs:send_text(6, "Waiting for pre-arm checks...")
        return false
    end

    local init_ok = ahrs:initialised()
    if not init_ok then
        gcs:send_text(6, "Waiting for initialisation...")
        return false
    end

    return true
  end

function update()
    local now = millis()
    local pos = ahrs:get_relative_position_NED_home()

    -- Stage 0: Arm, wait for position + 3D fix, then takeoff
    if stage == 0 then
      gcs:send_text(6, "Stage 0: Waiting for GPS, EKF and pre-arm checks...")
      if not arming:is_armed() then
        arming:arm()
        return update, 1000
      end

      if not readyToArm() then
          gcs:send_text(6, "Waiting for GPS, EKF and pre-arm checks…")
          return update, 1000
        end

      initial_alt = -pos:z()
      gcs:send_text(6, string.format("Armed. Initial Alt = %.1f m", initial_alt))

      if vehicle:set_mode(MODE_GUIDED) and vehicle:start_takeoff(target_alt) then
        gcs:send_text(6, "Takeoff started…")
        stage = 1
      else
        gcs:send_text(6, "Failed to start guided takeoff.")
      end
      return update, 1000
    end

    -- Stage 1: Wait for climb to complete (10m above initial)
    if stage == 1 then
        gcs:send_text(6, "Stage 1: Climbing to target altitude...")
        local pos = ahrs:get_relative_position_NED_home()
        if pos then
            local current_alt = -pos:z()
            gcs:send_text(6, string.format("Ascending... Alt = %.2f / %.2f", current_alt, initial_alt + target_alt))

            if current_alt >= initial_alt + target_alt - 0.5 then
                gcs:send_text(6, "Reached target. Switching to ALTHOLD for holding altitude...")
                stage = 2
            end
        end
        return update, 1000
    end
    
    -- Stage 2: switch back to GUIDED and move north at 2 m/s
    if stage == 2 then
        gcs:send_text(6, "Stage 2: Switching to GUIDED and moving north...")
        gcs:send_text(6, "Now moving north east at 2 m/s...")

        local target_vel = Vector3f()
        target_vel:x( -2.0 )    -- 2 m/s toward geographic south
        target_vel:y( -2.0 )    -- 2 m/s toward geographic west
        target_vel:z( 0.0 )    -- hold altitude

        if vehicle:set_target_velocity_NED(target_vel) then
          gcs:send_text(6, "Moving south west at 2 m/s")
        else
          gcs:send_text(6, "Velocity command failed")
        end

        -- wait for 10 seconds before switching to stage 3
        hover_start = millis()
        if now - hover_start > hover_duration then
            gcs:send_text(6, "Reached target. Switching to LAND...")
            stage = 3
        end

        return update, 1000
      end

    -- Stage 3: go to this coordinate 50.101298, -110.738011
    if stage == 3 then
        gcs:send_text(6, "Stage 3: Going to target coordinate...")
        local target_lat = 50.101298
        local target_lon = -110.738011

        if flyTo(target_lat, target_lon, target_alt) then
            gcs:send_text(6, string.format("Arrived at %.6f, %.6f", target_lat, target_lon))
            goto_stage = 0
            start_lat = target_lat
            start_lon = target_lon
            stage = 4
        else
            gcs:send_text(6, "Failed to go to target.")
        end

        return update, 1000

    end

    -- Stage 4: build the survey grid
    if stage == 4 then
      if not survey_gen then
        survey_gen    = survey_chunks_generator(
                          start_lat, start_lon,
                          boundaries.soft,
                          boundaries.hard,
                          target_length,
                          target_alt
                        )
        survey_points = {}
        survey_index  = 1
        survey_state  = 0
      end
    
      -- generate up to 5 new points
      for i=1,5 do
        local pt = survey_gen()
        if not pt then
          survey_gen = nil  -- done
          break
        end
        table.insert(survey_points, pt)
      end
    
      -- still building?
      if survey_gen then
        return update, 200
      end
    
      -- finished generating
      gcs:send_text(6, string.format("Survey: %d chunks to visit", #survey_points))
      export_chunks_to_kml("/survey_chunks.kml")
      stage = 5
      return update, 500
    end

    -- Stage 5: fly to each chunk center in turn
    if stage == 5 then
      if survey_index > #survey_points then
        gcs:send_text(6, "All chunks visited, landing…")
        stage = 6
        return update, 1000
      end

      local pt = survey_points[survey_index]

      -- fly to chunk center
      if survey_state == 0 then
        gcs:send_text(6, string.format("Heading to chunk %d/%d", survey_index, #survey_points))
        if flyTo(pt.lat, pt.lon, target_alt) then
          survey_hover_start = millis()
          survey_state = 1
          gcs:send_text(6, string.format("Hovering chunk %d/%d", survey_index, #survey_points))
        end
        return update, 200
      end

      -- hover for 5s
      if survey_state == 1 then
        if millis() - survey_hover_start >= 5000 then
          survey_index = survey_index + 1
          survey_state = 0
        end
        return update, 200
      end
    end

    -- Stage 6: Go to home coordinates 50.0973425,-110.7352315
    if stage == 6 then
      gcs:send_text(6, "Stage 6: Going to target coordinate for landing...")
      local target_lat = 50.0973425
      local target_lon = -110.7352315

      if flyTo(target_lat, target_lon, target_alt) then
          gcs:send_text(6, string.format("Arrived at %.6f, %.6f", target_lat, target_lon))
          goto_stage = 0
          stage = 7
      else
          gcs:send_text(6, "Failed to go to target.")
      end
      return update, 1000
    end

    -- Stage 7: Land
    if stage == 7 then
      gcs:send_text(6, "Stage 7: Landing...")
      local pos = ahrs:get_relative_position_NED_home()
      if pos then
          local current_alt = -pos:z()
          gcs:send_text(6, string.format("Descending... Alt = %.2f / %.2f", current_alt, target_alt))

          if current_alt <= target_alt + 0.5 then
              gcs:send_text(6, "Reached target. Switching to LAND...")
              vehicle:set_mode(MODE_LAND)
              if current_alt <= 0.5 then
                  gcs:send_text(6, "Drone landed")
                  arming:disarm()
                  stage = 8
              end
          end
      end
    end

    return update, 1000
end

return update()