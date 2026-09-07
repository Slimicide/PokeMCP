import argparse
import atexit
from io import BytesIO
from mcp.server.mcpserver import MCPServer, Image
from PIL import Image as PILImage
from .mGBA_client import Client, Move, Control, Direction, PKMN_E_FRAMES_WALK, MGBA_RELEASE_FRAMES, PKMN_E_FRAMES_FAST_TEXT_FILL
from .session import Session
from .overlay import draw_grid, upscale, read_dialogue, isolate_dialogue, in_dialogue, in_battle_dialogue
from os import path, remove, mkdir
from time import sleep
from difflib import SequenceMatcher
from typing import Optional

ASSUMED_FPS = 60

PROJECT_PATH = path.join(path.dirname(path.abspath(__file__)), "..")

GAMESTATE_SCREENSHOT_PATH =  path.join(PROJECT_PATH, "gamestate")
GAMESTATE_SCREENSHOT_RAW_PATH = path.join(GAMESTATE_SCREENSHOT_PATH, "gamestateRaw.png")

if not path.exists(GAMESTATE_SCREENSHOT_PATH):
    mkdir(GAMESTATE_SCREENSHOT_PATH)

currentSession = None
mGBAClient = None

mcp = MCPServer("mGBA-MCP")

def main():
    global currentSession
    global mGBAClient

    parser = argparse.ArgumentParser()
    parser.add_argument("--session-name", type=str, required=False, default="default", help="Use the session folder named <session-name>, will create the session folder if one does not exist.")
    parser.add_argument("--mcp-host", type=str, required=False, default="127.0.0.1", help="Address to bind MCP server to. (Default: 127.0.0.1)")
    parser.add_argument("--mcp-port", type=int, required=False, default=6001, help="Port to bind MCP server to. (Default: 6001)")
    parser.add_argument("--mgba-host", type=str, required=False, default="127.0.0.1", help="mGBA_server.lua socket address. (Default: 127.0.0.1)")
    parser.add_argument("--mgba-port", type=int, required=False, default=1337, help="mGBA_server.lua socket port. (Default: 1337)")
    args = parser.parse_args()

    mGBAClient = Client(args.mgba_host, args.mgba_port)

    currentSession = Session(PROJECT_PATH, args.session_name.lower())
    atexit.register(currentSession.update_save)

    mcp.run(transport="streamable-http", host="127.0.0.1", port=6001)

def return_image_to_model(image: PILImage) -> Image:
    buf = BytesIO()
    image.save(buf, format="PNG")
    return Image(data=buf.getvalue(), format="png")

def fetch_grid_screenshot() -> PILImage:
    """
    Returns a full game screenshot with a grid overlay.
    Also takes the opportunity to look for an updated save file.
    """
    return draw_grid(pil_screenshot())

def fetch_dialogue() -> PILImage:
    """
    Returns a cropped screenshot showing only dialogue content.
    """
    return isolate_dialogue(pil_screenshot())

def pil_screenshot(output_str: str = None):
    """
    Fetches a screenshot but keeps it as a PIL.Image object so other functions can use it in-memory.
    """
    # Clear old screenshots
    if path.exists(GAMESTATE_SCREENSHOT_RAW_PATH):
        remove(GAMESTATE_SCREENSHOT_RAW_PATH)

    controls = []
    controls.append({"key": ["SCREENSHOT"], "frames": 1})
    
    mGBAClient.send_controls(controls)

    # Check for game save updates
    if currentSession:
        currentSession.update_save()
    
    # Wait for screenshot from emulator.
    while not path.exists(GAMESTATE_SCREENSHOT_RAW_PATH):
        pass
    
    image = upscale(GAMESTATE_SCREENSHOT_RAW_PATH)
    remove(GAMESTATE_SCREENSHOT_RAW_PATH)

    if output_str:
        image.save(output_str)

    return image

@mcp.tool()
def process_dialogue() -> str:
    """
    Call this tool as soon as you enter any form of uninteractive dialogue, even if you anticipate it is the last line of dialogue.
    The only exception to this is if you need to make a choice. If you see a choice, take the controls and make it.
    It will cycle through the lines and return the full transcript.
    Ensure you use the `screenshot` tool immediately afterwards so you can retake control of the game.

    NOTE: This tool uses OCR to read text, sometimes it makes mistakes.
    If a letter seems of place, you will have enough context in the sentence to figure out what it really says.
    For instance, "I'm" sometimes reads as "T'm" due to an OCR error, but it's clear what it's intended to be.
    """
    dialogue = []

    corrections = {
        "POUREMON": "POKEMON",
        "POREMON": "POKEMON",
        "PUREMON": "POKEMON",
        "20b2HG00M\\": "ZIGZAGOON",
        "TAIEELE": "TACKLE",
        "tainted": "fainted",
        "Pointe": "Points",
        " T ": " I ",
        "+": "",
        "4": "a",
        "*": "",
        "'*": "",
        "#": "",
        "[ve": "I've",
        "You re ": "You're ",
        " you re ": " you're ",
        "Tf": "If",
        "T'm": "I'm",
        "Hawe": "Have",
        "hawe": "have"
    }

    _screenshot = pil_screenshot()

    while in_dialogue(_screenshot) or in_battle_dialogue(_screenshot):
        rawDialogue = read_dialogue(fetch_dialogue())

        for line in rawDialogue.split("\n"):
            line = line.strip()

            for correction in corrections:
                if correction in line:
                    line = line.replace(correction, corrections[correction])

            if len(dialogue) > 0:
                # Check if "line" has already been added, accounting for OCR errors between them
                if SequenceMatcher(None, line, dialogue[-1]).ratio() >= 0.85:
                    continue

            dialogue.append(line)

        mGBAClient.send_controls([{"key": ["A"], "frames": 1}])

        sleep(PKMN_E_FRAMES_FAST_TEXT_FILL / ASSUMED_FPS)
        _screenshot = pil_screenshot()

    return " ".join(dialogue)

@mcp.tool()
def screenshot(overlayGrid: Optional[bool] = True) -> Image | str:
    """
    Request a screenshot of the current gamestate from the emulator.
    This tool should only really be used to get an initial game screenshot or if your current game image appears to be mid transition.
    Your other tools that interact with the game will automatically provide you with a screenshot making this tool unnecessary during active gameplay.
    """
    result = None

    if overlayGrid:
        result = return_image_to_model(fetch_grid_screenshot())
    else:
        result = return_image_to_model(pil_screenshot())

    return result
    

@mcp.tool()
def walk(steps: list[Move], endFacingDirection: Optional[Direction] = None, endInteract: Optional[bool] = False) -> Image:
    """
    Walk through the game world.
    Optionally walk over to something with the intention of interacting with it.
    
    steps:
        Directions: {"UP", "DOWN", "LEFT", "RIGHT"}
        Tiles: Number of tiles you want to move in one direction

        Example: [{"direction": "UP", "tiles": 5}, {"direction": "RIGHT", "tiles": 10}]
            The player will walk UP 5 tiles and then walk RIGHT for 10 tiles.
    
    endFacingDirection (OPTIONAL):
        Optionally change the direction your character is facing after walking.
        Ignore this parameter if you are not intentionally walking adjacent to something you want to face and interact with.

    endInteract (OPTIONAL):
        Optionally interact with something after walking.
        Ignore this parameter if you are not intentionally walking adjacent to something you want to face and interact with.
    """
    result = None
    controls = []
    waitFrames = 0
    for step in steps:
        controls.append({"key": [step["direction"]], "frames": step["tiles"] * PKMN_E_FRAMES_WALK})
        waitFrames += step["tiles"] * PKMN_E_FRAMES_WALK
        waitFrames += MGBA_RELEASE_FRAMES

    if endFacingDirection:
        controls.append({"key": [endFacingDirection], "frames": 1})
        waitFrames += MGBA_RELEASE_FRAMES

    if endInteract:
        controls.append({"key": ["A"], "frames": 1})
        waitFrames += MGBA_RELEASE_FRAMES

    waitFrames += ASSUMED_FPS * 2 # Allow an additional two seconds for potential scene transition or interaction

    mGBAClient.send_controls(controls)
    sleep(waitFrames / (ASSUMED_FPS * 2))

    _screenshot = pil_screenshot()
    if in_dialogue(_screenshot):
        result = process_dialogue()
    else:
        result = return_image_to_model(fetch_grid_screenshot())

    return result

@mcp.tool()
def raw_input(inputs: list[Control]) -> Image:

    """
    Access all emulator keys. Any combination of GBA keys can be pushed individually or simultaneously.
    This function is primarily to navigate menus, fight battles, advance dialogue and interact with things in the game world.

    Keys: {"A", "B", "START", "SELECT", "RIGHT", "LEFT", "UP", "DOWN", "R", "L"}
    Frames: Number of frames to hold chosen key[s] down for. `1` is recommended in most cases unless you have an explicit reason to need more.

    Single simultaneous input example: [{"key": ["B", "RIGHT"], "frames": 1}]
    Single individual input example: [{"key": ["A"], "frames": 1}]

    Batched simultaneous input example: [{"key": ["A", "B"], "frames": 20}, {"key": ["A", "B", "START", "SELECT"], "frames": 1}]
    Batched single input example: [{"key": ["SELECT"], "frames": 1}, {"key": ["START"], "frames": 1}]
    """
    result = None
    waitFrames = ASSUMED_FPS * 2

    mGBAClient.send_controls(inputs)
    sleep(waitFrames / ASSUMED_FPS)

    _screenshot = pil_screenshot()

    if in_dialogue(_screenshot) or in_battle_dialogue(_screenshot):
        result = process_dialogue()
    else:
        result = return_image_to_model(pil_screenshot())

    return result

@mcp.tool()
def read_journal() -> str:
    """
    Read the model's game journal detailing its game progress.
    """
    with open(currentSession.journalPath, "r") as f:
        return f.read()

@mcp.tool()
def write_journal(content: str) -> str:
    """
    Write `content` to the model's game journal to update it.
    Make sure you first use the `read_journal` tool before you overwrite it.
    """
    with open(currentSession.journalPath, "w") as f:
        f.write(content)

    return "Updated game journal."


if __name__ == "__main__":
    main()