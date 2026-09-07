import socket
from typing import Literal, TypedDict

# Arbitrary number - must correspond to `local releaseDelay` in mGBA_server.lua assigned in the per-frame callback.
# Dictates how long to "let go" of the controls in between inputs so it's not a constant stream of frame-perfect inputs.
MGBA_RELEASE_FRAMES = 10

# Full animation cycle frames
PKMN_E_FRAMES_WALK = 16
PKMN_E_FRAMES_TURN = 8

PKMN_E_FRAMES_FAST_TEXT_FILL = 120

Direction = Literal["RIGHT", "LEFT", "UP", "DOWN"]
Button = Literal["A", "B", "START", "SELECT", "R", "L"]

class Control(TypedDict):
    key: list[Direction | Button]
    frames: int

class Move(TypedDict):
    direction: Direction
    tiles: int

class EndFaceDirection(TypedDict):
    faceDirection: Literal["RIGHT", "LEFT", "UP", "DOWN", None]

class Client:
    def __init__(self, host: str = "127.0.0.1", port: int = 1337):
        self.host = host
        self.port = port
        self.sock = None

    def ensure_connection(self):
        if self.sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            self.sock = sock
        return self.sock

    def send_controls(self, controls: list[Control]):
        # Protocol <KEY[,KEY...]> <FRAMES><SEPARATOR>
        # Examples:
        #   A 14|
        #   START 1|
        #   A,SELECT 20|
        
        command = ""
        for control in controls:
            for index, key in enumerate(control['key']):
                command += key
                command += ',' if index != len(control['key']) - 1 else ' '
            command += str(control['frames'])
            command += '|'

        self.ensure_connection()
        self.sock.sendall(command.encode("UTF-8"))