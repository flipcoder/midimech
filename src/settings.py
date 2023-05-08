from dataclasses import dataclass

@dataclass
class DeviceSettings:
    row_offset: int
    octave: int
    transpose: int
    bend: int

