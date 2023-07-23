from dataclasses import dataclass

@dataclass
class DeviceSettings:
    row_offset: int
    column_offset: int
    octave: int
    transpose: int
    bend: int

class Device:
    def __init__(self, core):
        self.core = core
        self.octave = 0
        self.transpose = 0

