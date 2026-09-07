from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
import sys
import pytesseract

"""
This file was mostly the work of AI and I had very little to do with it besides tidying up.
"""

SCREEN_W = 240
SCREEN_H = 160

# Pokémon Emerald overworld metatile size.
TILE_SIZE = 16

# Upscale the screenshot before drawing.
SCALE = 6

def upscale(rawGameScreenshotPath: str, output_path: str = None):
    """
    Takes a native GameBoy screenshot and upscales it.
    """
    image = None
    
    while image is None:
        try:
            image = Image.open(rawGameScreenshotPath).convert("RGB")
        except UnidentifiedImageError: # Synchronizaiton issues between mGBA_server and mGBA_mcp
            pass

    if image.size != (SCREEN_W, SCREEN_H):
        raise ValueError(
            f"Expected {SCREEN_W}x{SCREEN_H}, "
            f"got {image.width}x{image.height}"
        )

    # Upscale using nearest-neighbor so pixel art stays crisp.
    image = image.resize(
        (SCREEN_W * SCALE, SCREEN_H * SCALE),
        Image.Resampling.NEAREST,
    )

    # Crop out incomplete squares from top and bottom
    w, h = image.size
    image = image.crop((0, 32, w, h - 30))

    if output_path:
        image.save(output_path)

    return image

def isolate_dialogue(upscaledGameScreenshot: Image, output_path: str = None):
    """
    Crops an upscaled game screenshot to isolate the screen location that contains dialogue.
    """
    # Dialogue box region in the original 240x160 screenshot
    x1, y1 = 12, 112
    x2, y2 = 225, 149
    
    dialogueBox = upscaledGameScreenshot.crop((
        x1 * SCALE,
        y1 * SCALE,
        x2 * SCALE,
        y2 * SCALE,
    ))

    if output_path:
        dialogueBox.save(output_path)

    return dialogueBox

def read_dialogue(isolatedDialogue: Image):
    """
    Runs (flawed) OCR to read game dialogue from a cropped game screenshot.
    """
    return pytesseract.image_to_string(isolatedDialogue, config="--psm 6").strip().encode("ascii", errors="ignore").decode("ascii")

def pending_choice(upscaledGameScreenshot: Image, match_threshold: float = 0.8) -> bool:
    """
    Returns True if a choice box is present in the provided game screenshot.
    Returns False if no choice is pending
    """
    CHOICE_BORDER_COLOR = (115, 107, 132)
    CHOICE_BORDER_TOLERANCE = 15
    
    # Native-resolution (BORDER_Y, X1, X2) for each known choice box position
    CHOICE_BOX_POSITIONS = [
        {"name": "top_left",     "y": 30, "x1": 20,  "x2": 76},
        {"name": "bottom_right", "y": 63, "x1": 164, "x2": 212},
        {"name": "battle_right", "y": 63, "x1": 196, "x2": 236},
    ]
    
    for pos in CHOICE_BOX_POSITIONS:
        choiceStrip = upscaledGameScreenshot.crop((
            pos["x1"] * SCALE,
            pos["y"] * SCALE,
            pos["x2"] * SCALE,
            pos["y"] * SCALE + 2,
        ))
    
        choicePixels = list(choiceStrip.getdata())
        choiceMatches = sum(
            1 for (r, g, b) in choicePixels
            if abs(r - CHOICE_BORDER_COLOR[0]) <= CHOICE_BORDER_TOLERANCE
            and abs(g - CHOICE_BORDER_COLOR[1]) <= CHOICE_BORDER_TOLERANCE
            and abs(b - CHOICE_BORDER_COLOR[2]) <= CHOICE_BORDER_TOLERANCE
        )

        # Iterate through all choice box positions to see if any are pending
        if (choiceMatches / len(choicePixels)) >= match_threshold:
            return True

    # No choice boxes found
    return False

def in_dialogue(upscaledGameScreenshot: Image, match_threshold: float = 0.8) -> bool:
    """
    Returns True if a dialogue box is present in the provided game screenshot.
    Returns False if no dialogue box is present.
    """
    # Checking for a thin teal strip along the text box border
    BORDER_COLOR = (0, 255, 156)
    BORDER_TOLERANCE = 20   # per-channel tolerance
    BORDER_Y = 110           # native-resolution row where the teal border line sits
    BORDER_X1, BORDER_X2 = 15, 225

    dialogueStrip = upscaledGameScreenshot.crop((
        BORDER_X1 * SCALE,
        BORDER_Y * SCALE,
        BORDER_X2 * SCALE,
        BORDER_Y * SCALE + 2,  # couple px tall for margin
    ))

    dialoguePixels = list(dialogueStrip.getdata())
    dialogueMatches = sum(
        1 for (r, g, b) in dialoguePixels
        if abs(r - BORDER_COLOR[0]) <= BORDER_TOLERANCE
        and abs(g - BORDER_COLOR[1]) <= BORDER_TOLERANCE
        and abs(b - BORDER_COLOR[2]) <= BORDER_TOLERANCE
    )

    # Return control to the player if they need to make a choice.
    if pending_choice(upscaledGameScreenshot):
        return False

    return (dialogueMatches / len(dialoguePixels)) >= match_threshold

def in_battle_dialogue(upscaledGameScreenshot: Image, match_threshold: float = 0.8) -> bool:
    """
    Returns True if there is battle dialogue present in the provided game screenshot.
    Returns False if the user isn't receiving battle dialogue or has to make a choice (likely naming a caught Pokemon).

    Battle dialogue example: POOCHYENA used SCRATCH! MUDKIP's attack missed! TORCHIC gained 17 EXP. Points!
    """
    # Checking for a thin maroon/red strip along the battle text box border
    BORDER_COLOR = (214, 74, 57)
    BORDER_TOLERANCE = 20   # per-channel tolerance
    BORDER_Y = 110           # native-resolution row where the border line sits (same row as dialogue box)
    BORDER_X1, BORDER_X2 = 15, 225

    strip = upscaledGameScreenshot.crop((
        BORDER_X1 * SCALE,
        BORDER_Y * SCALE,
        BORDER_X2 * SCALE,
        BORDER_Y * SCALE + 2,
    ))

    pixels = list(strip.getdata())
    matches = sum(
        1 for (r, g, b) in pixels
        if abs(r - BORDER_COLOR[0]) <= BORDER_TOLERANCE
        and abs(g - BORDER_COLOR[1]) <= BORDER_TOLERANCE
        and abs(b - BORDER_COLOR[2]) <= BORDER_TOLERANCE
    )

    # Return control to the player if they need to make a choice.
    if pending_choice(upscaledGameScreenshot):
        return False

    return (matches / len(pixels)) >= match_threshold

def draw_grid(image: Image, output_path: str = None):
    """
    Draws a high contrast pink grid where 1 square = 1 game tile to help models visualize space.
    Optionally enable coordinates for each square to help plan paths (seems to cause more problems than solve)
    """
    # ============================================================
    # Configuration
    # ============================================================

    # Adjust these until the grid lines perfectly match the game grid.
    # Values are in ORIGINAL 240x160 pixels.
    OFFSET_X = -0.3
    OFFSET_Y = 2.8

    # Set to False if you don't want coordinate labels.
    SHOW_COORDINATES = False

    # Change 0,0 origin to player's current location.
    CENTER_PLAYER = True
    # Without changing origin, player stands in 7,4
    CENTER_COL = 7
    CENTER_ROW = 4

    # Grid appearance
    GRID_COLOR = (255, 0, 255)
    GRID_WIDTH = 2

    TEXT_COLOR = (255, 255, 0)
    TEXT_BACKGROUND = (0, 0, 0)

    #   ============================================================

    draw = ImageDraw.Draw(image)

    tile = TILE_SIZE * SCALE
    offset_x = OFFSET_X * SCALE
    offset_y = OFFSET_Y * SCALE

    if SHOW_COORDINATES:
        try:
            font = ImageFont.truetype(
                "DejaVuSans-Bold.ttf",
                7 * SCALE
            )
        except OSError:
            font = ImageFont.load_default()

    # Draw vertical grid lines.
    x = offset_x
    while x <= SCREEN_W * SCALE:
        draw.line(
            [(x, 0), (x, SCREEN_H * SCALE)],
            fill=GRID_COLOR,
            width=GRID_WIDTH,
        )
        x += tile

    # Draw horizontal grid lines.
    y = offset_y
    while y <= SCREEN_H * SCALE:
        draw.line(
            [(0, y), (SCREEN_W * SCALE, y)],
            fill=GRID_COLOR,
            width=GRID_WIDTH,
        )
        y += tile

    # Draw coordinates.
    if SHOW_COORDINATES:
        # Determine the coordinate of each visible cell.
        start_col = -(offset_x // tile)
        start_row = -(offset_y // tile)

        # We use the grid's logical coordinates rather than
        # simply numbering from the top-left screenshot pixel.
        for row in range(-1, (SCREEN_H * SCALE // tile) + 2):
            for col in range(-1, (SCREEN_W * SCALE // tile) + 2):

                left = offset_x + col * tile
                top = offset_y + row * tile

                right = left + tile
                bottom = top + tile

                # Skip cells completely outside the image.
                if right < 0 or left > SCREEN_W * SCALE:
                    continue
                if bottom < 0 or top > SCREEN_H * SCALE:
                    continue

                # Choose whether to put the player at 0,0 or not. Also make the upwards direction a positive number
                if CENTER_PLAYER:
                    label = f"{col - CENTER_COL} , {-(row - CENTER_ROW)}"
                else:
                    label = f"{col} , {-(row)}"

                bbox = draw.textbbox((0, 0), label, font=font)
                label_w = bbox[2] - bbox[0]
                label_h = bbox[3] - bbox[1]

                tx = min(right - label_w - 3, SCREEN_W * SCALE - label_w - 1)
                ty = min(bottom - label_h - 3.5, SCREEN_H * SCALE - label_h - 1)

                bbox = draw.textbbox((tx, ty), label, font=font)

                # Small opaque background so the number remains readable.
                draw.rectangle(
                    (
                        bbox[0] - 1,
                        bbox[1] - 1,
                        bbox[2] + 1,
                        bbox[3] + 1,
                    ),
                    fill=TEXT_BACKGROUND,
                )

                draw.text(
                    (tx, ty),
                    label,
                    fill=TEXT_COLOR,
                    font=font,
                )

    # Crop out incomplete squares from top and bottom
    w, h = image.size
    image = image.crop((0, 30, w, h - 16))

    if output_path:
        image.save(output_path)

    return image