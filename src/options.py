from dataclasses import dataclass

@dataclass
class Options:
    version: int = 0
    lights: str = "4,7,3,7,3,3,7,3,7,3,7,3"
    colors: str = "red,darkred,orange,goldenrod,yellow,green,darkolivegreen,blue,darkslateblue,indigo,darkorchid,pink"
    split_lights: str = "4,7,5,7,5,5,7,5,7,5,7,5"
    one_channel: int = 0
    lite: bool = False # lite mode (no gfx)
    velocity_curve: float = 1.0
    velocity_curve_low: float = 0.5
    velocity_curve_high: float = 3.0
    min_velocity: float = 0
    max_velocity: float = 127
    show_lowest_note: bool = False
    mpe: bool = True
    hardware_split: bool = False
    midi_out: str = "midimech"
    split_out: str = "split"
    fps: int = 60
    split: bool = False
    foot_in: str = ""
    sustain: float = 1.0
    sustain_split: str = "both"
    size: int = 128
    width: int = 16
    height: int = 8
    vibrato: str = 'mod'
    jazz: bool = False
    chord_analyzer: bool = True

DEFAULT_OPTIONS = Options()

