-- Modify to change socket information.
local host = "127.0.0.1"
local port = 1337
--

local screenshotDir = debug.getinfo(1, "S").source:sub(2):match("(.*/)") .. "gamestate/"
local gamesDir = debug.getinfo(1, "S").source:sub(2):match("(.*/)") .. "games/"

-- https://mgba.io/docs/scripting.html#constant-GBA_KEY
local KEY_CONSTANTS = {
    A      = C.GBA_KEY.A,       -- 0
    B      = C.GBA_KEY.B,       -- 1
    SELECT = C.GBA_KEY.SELECT,  -- 2
    START  = C.GBA_KEY.START,   -- 3
    RIGHT  = C.GBA_KEY.RIGHT,   -- 4
    LEFT   = C.GBA_KEY.LEFT,    -- 5
    UP     = C.GBA_KEY.UP,      -- 6
    DOWN   = C.GBA_KEY.DOWN,    -- 7
    R      = C.GBA_KEY.R,       -- 8
    L      = C.GBA_KEY.L,       -- 9
}

function screenshot()
    emu:screenshot(screenshotDir .. "gamestateRaw.png")
end

function controller(message, inputQueue)
    for command in message:gmatch("[^|]+") do
        local keyPart, frames = command:match("(%S+)%s+(%d+)")

        local bits = {}
        for key in keyPart:gmatch("[^,]+") do
            if KEY_CONSTANTS[key] then
                table.insert(bits, KEY_CONSTANTS[key])
            elseif key == "SCREENSHOT" then
                screenshot()
            else
                console:warn("[-] Invalid key: " .. key)
            end
        end

        if #bits > 0 then
            table.insert(inputQueue, {
                mask = util.makeBitmask(bits),
                frames = tonumber(frames),
            })
        end
    end
end

-- https://mgba.io/docs/scripting.html#lua-root-socket
local server, err = socket.bind(host, port)
if err then
    console:error("[!] Bind failed: " .. tostring(err))
    return
end

local listening, err = server:listen()
if err then
    console:error("[!] Listening failed: " .. tostring(err))
    return
end

local banner = [[

                 ⢠⠞⠉⠉⢳
                 ⢸⡀⠀⠀⣠⡇
                  ⠙⡖⢾⠋
                  ⢸⠁⠸⡄
                  ⡞⠀⠀⣇
    ⢰⠒⠒⠒⠒⠒⠒⠲⠲⠚⠓⠒⠒⠛⠓⢒⣖⠒⠒⠒⠒⠒⠒⢲
    ⣼⠀⠀⠀⠀   ⢠⠖⠋⠉⠷⣄⠀⠀⢠⠖⠉⠉⠑⢦⠀⠀⠀⢸            SERVER LIVE AND READY
    ⡟⠉⢻⠀⠀⠀⠀ ⣿⣾⣿⣦⡀⢸⠀⠀⢿⣿⣿⣷⡀⢸⠀⠀ ⢸⠋⠙⡇
    ⡇⠀⢸⠀⠀⠀  ⠘⢿⣿⢟⣂⠞⠀⠀⠈⠿⣿⣿⣡⠞⠀⠀⠀⢸⠀⠀⡇
    ⡇⣾⠉⠉⠙⢧⡀⠀                   ⣠⠞⠉⠉⡙
    ⠉⣻⠀⠀⠀⠀⠙⢦⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣠⠞⠁⠀⠀⠀  ⡏         > HOST %s
     ⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    ⡇          > PORT %s
     ⠿⡤⣤⣤⣤⣤⣤⣤⣤⣤⣤⢤⠤⠤⠤⠤⢤⣤⣤⣤⣤⣤⣤⡤⢤⣤⠇

]]

console:log(banner:format(host, port))

local inputQueue = {}
local currentInput = nil
local inputFramesRemaining = 0

local releaseBufferActive = false
local releaseDelay = 0

-- Called after new save file update
callbacks:add("savedataUpdated", function()
    io.open(gamesDir .. "savefileUpdated", "w"):close()
end)

-- Called once per frame
callbacks:add("frame", function()

    -- Input is currently happening this frame
    if currentInput then
        inputFramesRemaining = inputFramesRemaining - 1

        if inputFramesRemaining == 0 then
            emu:clearKeys(currentInput.mask)
            currentInput = nil

            -- Leave a buffer without any inputs to allow the finished input to take effect
            releaseBufferActive = true
            releaseDelay = 10 -- Can change later, holds 10 frames of non-input between inputs
        end
    end

    -- There is currently no input happening this frame
    if not currentInput then
        if not releaseBufferActive then
            currentInput = table.remove(inputQueue, 1) -- Check the queue for more input

            if currentInput then -- New input found in the queue
                inputFramesRemaining = currentInput.frames
                emu:addKeys(currentInput.mask)
            end
        else
            releaseDelay = releaseDelay - 1
            if releaseDelay == 0 then
                releaseBufferActive = false
            end
        end
    end

    if server:hasdata() then
        local client, err = server:accept()
        if err then
            console:error("[!] Client connection failed: " .. tostring(err))
        end

        if client then
            console:log("[+] Client connected.")

            client:add("received", function()
                local input, err = client:receive(4096)
                if input then
                    controller(input, inputQueue)
                end
            end)
        end
    end
end)