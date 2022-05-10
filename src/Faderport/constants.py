from enum import Enum

"""
0x47 - Manufacturers ID
0x7F - System Exclusive Device ID
0x15 - Product model ID
record sysex data=(127,127,6,6)

0x00, 0x01, 0x06 - Manufacturers ID
0x02 - Product model ID Faderport 8
"""
SYSEX_PREFIX_FADERPORT = [0x00, 0x01, 0x06, 0x02]


class MIDIType(Enum):
    ControlChange = 0
    Note = 1
    Pitch = 3
    Touch = 4


class LightTypes(Enum):
    White = 0
    Red = 1
    Green = 2
    Yellow = 3
    Blue = 4
    RGB = 6
    NoLight = 7


class ColorsSingle(Enum):
    Black = 0
    LitBlink = 1
    Lit = 2
