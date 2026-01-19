from dataclasses import dataclass

@dataclass
class Settings:
    version: int = 0 # Version of the program (not yet impl)
    # lights: str = "4,7,3,7,3,3,7,3,7,3,7,3"

    # LinnStrument light numbers
    # lights: str = "4,7,3,7,3,3,7,3,7,3,7,3"
    # Same as above, for split
    lights: str = "1,9,9,2,2,3,3,5,8,8,11,11"
    split_lights: str = "4,7,5,7,5,5,7,5,7,5,7,5"
    
    # LinnStrument light color for mark, default: 1 (red)
    mark_light: int = 1
    
    # LaunchPad light color for mark, default: red
    mark_color: str = "red"
    
    # Color scheme using webcolors
    # split_colors: str = "cyan,blue,blue,blue,blue,blue,blue,blue,blue,blue,blue,blue"
    launchpad_colors: str = '5,1,9,1,13,122,1,37,45,94,1,95'
    
    colors: str = "red,darkred,orange,goldenrod,yellow,green,darkolivegreen,blue,darkslateblue,indigo,darkorchid,pink"
    # colors: str = "cyan,green,green,green,green,green,green,green,green,green,green,green"
    split_colors: str = "cyan,blue,blue,blue,blue,blue,blue,blue,blue,blue,blue,blue"

    # MPE Settings
    # one_channel==0: MPE enabled
    # one_channel==1: Output to channel 1 only
    # one_channel==2: Output to channel 2 only, ...
    one_channel: int = 0

    # lite mode (no extra gfx, less processing)
    lite: bool = False

    # Custom velocity curve exponent, ex: 0.5 = more sensitive
    velocity_curve: float = 1.0
    
    # Velocity curve exponent for foot controller curve bending
    velocity_curve_low: float = 0.5
    velocity_curve_high: float = 3.0

    # Clamp velocity
    min_velocity: float = 0
    max_velocity: float = 127
    
    # Show lowest note mark (old option, no longer maintained)
    show_lowest_note: bool = False

    # MPE mode on by default? (use one_channel instead)
    # mpe: bool = True

    # Automatically set based on size==200,
    #  but can be forced for testing purposes
    hardware_split: bool = False
    
    # Midi out device name, partial matches allowed
    midi_out: str = "midimech"
    
    # Split device name, partial matches allowed
    split_out: str = "split"

    # Application frames per second
    fps: int = 60

    # Start with split on?
    split: bool = False
    
    # Foot controller device name, partial matches allowed
    foot_in: str = ""
    
    # Sustain pedal value multiplier (not yet impl)
    sustain: float = 1.0

    # which split should sustain pedal use (left, right, both)
    sustain_split: str = "both"

    # Size of LinnStrument (128 or 200)
    size: int = 128

    # Right now these are calculated from size, don't use
    width: int = 16
    height: int = 8

    # launchpad viberato method (off, mod, or pitch)
    vibrato: str = 'mod'
    
    # Set scale based on left hand chord (not yet impl)
    jazz: bool = False
    
    chord_analyzer: bool = True

    # Allow Y axis to bend chromatically
    y_bend: bool = False

    bend_range: int = 24

    # Pitch bend scaling for mech layout (1.0 = no scaling, 2.0 = double)
    bend_scale: float = 1.0

    row_offset: int = 5
    column_offset: int = 2
    base_offset: int = 4

    # octave separation between multiple launchpads
    octave_separation: int = 1
    
    # octave splitting the linn and transposing octaves on the right side
    octave_split: int = 0

    # Software chromatic quantization (12-TET)
    # Snaps pitch bends to nearest semitone, allowing semitones between whole-tone pads.
    # Without quantization, every note has slight microtonal errors from human imprecision.
    # At this pad scale, you can only realistically aim for semitones or whole tones.
    # Hardware quantization only snaps to pad centers (whole tones), missing semitones.
    # This software quantization snaps to ALL 12 chromatic semitones.
    # REQUIRED: Set LinnStrument Quantize=OFF, Quantize Tap=OFF, Quantize Hold=OFF
    chromatic_quantize: bool = False
    
    # Whole tone bias: adjusts the rounding threshold between semitones and whole tones.
    # Range: -1.0 to 1.0
    #   0.0 = equal zones (50/50 split, standard rounding at 0.5 threshold)
    #   Positive = larger whole-tone zones (need to aim closer to center to hit semitones)
    #   Negative = larger semitone zones (easier to hit semitones accidentally)
    # Recommended: 0.4375 for LinnStrument speed bump surface
    whole_tone_bias: float = 0.0
    
    # Quantize Hold Threshold: movement sensitivity for vibrato (0 to 1)
    # Detects if you're wiggling (vibrato) vs holding still
    # 0 = always snap (even when moving)
    # 1 = never snap (all movement passes through as microtones)
    # 0.5 = balanced (moderate movement triggers vibrato)
    # Lower = need more aggressive movement to trigger vibrato
    quantize_hold_threshold: float = 0.0

DEFAULT_OPTIONS = Settings()

