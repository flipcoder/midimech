from src.device import Device, DeviceSettings

class Launchpad(Device):
    def __init__(self, out, mode, index, octave_separation=0):
        super().__init__()
        self.out = out
        self.mode = mode
        self.index = index
        self.octave_separation = octave_separation

