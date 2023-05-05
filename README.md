# midimech

![midimech](https://i.imgur.com/iNKaTi3.png)

**IN DEVELOPMENT**

Midimech is an alternative musical note layout system for the LinnStrument and LaunchPad X.  It uses a wholetone-based isomorphic layout.  I was surprised to find out this layout and its variants were not in common usage, despite being incredibly convincing.  Lacking an isomorphic controller, I used to map this layout to my mechanical keyboard to play.  Because of this, my friends and I referred to it as "playing the mech".  The layout could also be referred to as Wholetone +5 or Diagonal Wicki-Hayden but I still prefer calling it mech.

This project intends to bring the layout to wherever it is capable of being played, starting with the LinnStrument and Launchpad X.

Midimech supports:
- Usage as a virtual MIDI controller in your DAW
- Bigger range than the default LinnStrument layout
- Synthesia/DAW visualization for learning songs
- Diagonal split
- Transposing and Octave shifting
- Great for playing fast arpeggios and piano runs ;)

**Please read the instructions and important notes before usage.  Have fun!**

License: MIT

Copyright (c) 2023 Grady O'Connell

Please see the Attributions section below for a list of what powers this project!

*This project is not affiliated with Roger Linn Design.*

LinnStrument Community Discord: https://discord.gg/h2BcrzmTXe

![Screenshot](https://i.imgur.com/eYsl3T4.png)

## Video

[![Video](https://img.youtube.com/vi/GbkhwpPsbPo/0.jpg)](https://www.youtube.com/watch?v=GbkhwpPsbPo)

## Advantages

- Notes that sound good together are closer together.  Notes that sound worse are furthest apart.  Mistakes will be less likely and less obvious!
- Like the LinnStrument's layout, it is also isomorphic (the same chord and scale shapes can be played anywhere)
- The most common chords and scales are far easier to play and remember than other layouts.
- Extended range compared to standard +5 tuning, making room for using a split.
- Unlike piano, instrument splits can overlap.
- Less finger stretching than other layouts when playing chords, which may help ergonomically.
- Arpeggios are quite smooth, as you're simply walking stacked shapes.

## Chord Shapes

![Chord Shapes](https://i.imgur.com/DaqVFqP.png)

## Important Notes

So far, this has mostly been tested on the LinnStrument 128 version.  If you own the 200-note version, please feel free to test it and let me know how this works for you.

Midimech sends midi commands to your midi controller and does NOT replace the firmware of your device.  It changes certain settings for the program to function and resets them to common values after ending the program.

This program is *in development*, so some things may be buggy.  If a device persists in a different state after ending the program (such as if a crash occurs), try running the program again and closing it.  Otherwise try reconnecting or resetting it.

Because it changes the setup of the LinnStrument during usage, it is only recommended for people that are comfortable with setting up and configuring the Linnstrument.

That being said, I hope you enjoy it and have fun!

## Getting Started

### Latest Builds (Windows)

- [Download (Win)](https://github.com/flipcoder/midimech/releases)

Alternatively, you can use the process below to run it from the repository.

### Running from Git (for Mac/Linux)

- Download the project by typing the following commands in terminal:
```
git clone https://github.com/flipcoder/midimech
```

- Switch to the new project folder:
```
cd midimech
```

- Install the dependencies:
```
pip3 install -r requirements.txt
```

- Follow the **Setup** instructions described in the section below.

- When running the program, you can use:
```
python3 midimech.py
```

### Setup

- First create a midi loopback device.  You can do this easily with LoopMidi on Windows or using "Audio MIDI Setup / MIDI Studio" on Mac.  Then set your DAW to use this device instead of the linnstrument.  Make sure the virtual device you set up has "midimech" in its device name, since this is how its detected by the program.

- If you're using the LinnStrument 200, set `size=200` in your settings.ini.  If you don't have a settings file, copy it from settings.ini.example.

- Run midimech.  You should see a window pop up with the layout.

- Your Linnstrument or LaunchPad X should show the colors of the layout and be playable in your DAW.

- To enable the split, create another midi loopback device called "split" and restart midimech.  Click the SPLIT button.  One side should turn blue.

## How to Play

### Layout

Each row consists of a whole tone scale and each row is separated by fourths.  This has a number of advantages you'll see below.

### Basic Scales

The major/minor scales are shaped with the "3-4" pattern.  3 notes on first row, then 4 notes on next row, then repeat moving over 1 space, making runs fit across the fingers easily.
Here's what it looks like:

```
4567
123
```

All the modes for this, (such as lydian, dorian, etc.) are accessible by picking a different starting note.

For example, if you start the scale on 6, it becomes a minor scale.

### Pentatonic Scales

Similarly, the pentatonic scale modes fit the "2-3" pattern:

```
345
12
```

### Melodic Minor Scale

Melodic minor has a "2-5" pattern:

```
34567
 12
```

## More Scales

Once you become comfortable with this layout, you can introduce the harder scales into your playing:

### Blues Scale

Here's a fun one.  Depending on the virtual instrument used, I prefer to visualize the blues scale as a 2-3 pattern and bending into the "blue note".

The shape in that case is this:

```
345
12
```

The '2' in this shape is the tonic of the blues scale and the blue note is accessed by bending between 4 and 5.  When playing the scale, start on the note position labeled '2' above.  Note that the numbers here are just the numbers inside the shape in order, so they do not correspond with actual intervals.

To hold the blue note, simply wiggle your finger between 4 and 5 in the shape above or bend up from 4.  That usually sounds cool.

If you're playing an instrument without bend, the blues scale looks like this:

```
4 6
 235
  1
```

Or:

```
 6
235
 1  4
```

### Harmonic Major Scale

This is the same 3-4 pattern, but the 6th note is flat:

```
6
 45 7
 123
```

Or:

```
 45 7
 123  6
```

### Harmonic Minor Scale

This one is a little tricky at first:

```
 6
345 7
 12
```

Or:

```
7
 6
 345
  12
```

You might prefer to think about this as a mode of Ionian Augmented intead, which is the 3-4 shape but with a sharp 5:

```
5
 4 67
 123
```

Or:

```
 4 67
 123 5
```

## Circle of 5ths (Advanced)

### Key Signature

A benefit of this layout is the ability to identify and switch key signatures easily based on position.  As you shift to the left, you add flats.  To the right, you add sharps.  You walk these in a zig-zag motion between both whole tone scales.  Follow the shape of these numbers to see the pattern (from 1 to 7).

```
 2468
1357
```

If note 1 is C (no sharps or flats in key signature), moving to 3 adds 2 sharps to the key signature.  Simiarly if you're moving from 3 to 1, it adds two flats (or subtracts sharps).

### Brightness

Since the layout resembles the circle of 5ths, the further right you go from your tonic, the brighter than sound.  The further left, the darker the sound. This is because the layout resembles a staggered circle of 5ths which corresponds with musical brightness.

If you take the 3-4 pattern described above and shift your tonic inside of it, the further the tonic is to the left, the brighter the mode, from lydian all the way to locrian (left to right).  This happens with other scale shapes as well.


## Visualizer

### DAW visualization

Using this program, you can visualize the midi playing in your DAW on both the screen and LinnStrument.
You do this by creating another device in LoopMidi called "visualizer" then use a Midi Out plugin
on the track you want to visualize and set the plugin to use the visualizer midi device.

### Synthesia

To use the visualizer with Synthesia, create a new MIDI loopback device called "visualizer".
In Synthesia settings, set it as an output device for note lights.

## Future Plans

- Scale integration
- Touchscreen support
- Find a way to adjust vibrato sensitivity without affecting slides.  Roger Linn has indicated that this is probably impossible, but I have a few ideas to try.
- Better velocity curve settings (right now its only basic options in the settings.ini).
- Better GUI and integration with the settings file.

## Attributions

This program is built using the following projects and libraries:

- [Pygame](https://github.com/pygame/pygame)
- [Pygame_GUI](https://github.com/MyreMylar/pygame_gui)
- [RtMidi2](https://github.com/gesellkammer/rtmidi2)
- [PyMsgbox](https://github.com/asweigart/pymsgbox)
- [PyGLM](https://github.com/Zuzu-Typ/PyGLM)
- [Launchpad-Py](https://github.com/FMMT666/launchpad.py) by FMMT666 (CC Attribution)

Thank you!

## Contact / Questions

I'm on the LinnStrument Discord at https://discord.gg/h2BcrzmTXe.  Come hang out!



