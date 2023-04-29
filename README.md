# midimech

![midimech](https://i.imgur.com/iNKaTi3.png)

**IN DEVELOPMENT**

This program maps the LinnStrument, LaunchPad X, and your computer keyboard to use an isomorphic wholetone layout that I discovered years ago.  I was surprised to find out this layout and its variants were not in common usage, despite being incredibly easy to play.  I used to map this layout to my mechanical keyboard and just play it like that.  Because of this, my friends and I referred to it as "playing the mech", but
you could also call the layout Diagonal Wicki-Hayden, Wholetone, or whatever you like.  I prefer mech. 😎
This project intends to bring the layout to more people and I consider it a good proposal for next-gen instruments.

Midimech supports:
- Bigger range than the default LinnStrument layout
- Synthesia/DAW visualization for learning songs
- Diagonal split, which fits great even on the 128
- Transposing and Octave shifting
- LaunchPad X support (more devices coming in the future)
- And it's great for playing piano runs ;)

**Please read the instructions and important notes before usage.  Have fun!**

License: MIT

Copyright (c) 2023 Grady O'Connell

*This project is not affiliated with Roger Linn Design.*

LinnStrument Community Discord: https://discord.gg/h2BcrzmTXe

![Screenshot](https://i.imgur.com/eYsl3T4.png)

Launchpad Support powered by: [Launchpad-Py](https://github.com/FMMT666/launchpad.py)

## Video

[![Video](https://img.youtube.com/vi/GbkhwpPsbPo/0.jpg)](https://www.youtube.com/watch?v=GbkhwpPsbPo)

## Important Notes

So far, this has only been tested on the LinnStrument 128 version.  If you own the 200-note version, it's harder to set up, but please feel free to test it and let me know how this works for you.

This program is *experimental*, so some things will be buggy and tricky to get working.  Let me know if you run into any issues and follow the directions carefully.  If the wrong notes are playing, there's probably something wrong with the way you've set up the linnstrument during the instructions.  If a device persists in a different state after ending the program (such as if a crash occurs), simply reconnect it.  The LinnStrument also has a reset feature you may find useful.

And since this is experimental, please use it at your own risk and prepare to do basic troubleshooting to get it working.

## Setup

- First create a midi loopback device.  You can do this easily with LoopMidi on Windows or using "Audio MIDI Setup / MIDI Studio" on Mac.  Then set your DAW to use this device instead of the linnstrument.  Make sure the virtual device you set up has "midimech" in its device name, since this is how its detected by the program.

- Set your LinnStrument to use ChPerRow mode.  (Or alternatively, see the section *MPE* for getting the full MPE mode working).

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
pip install -r requirements.txt
```

- Run midimech.py.  You should see a window pop up with the layout.

- If this works, your linnstrument will show the colors of the layout and be playable in your DAW.

- If you're using the larger (200-note) version of the LinnStrument, click "SIZE" to use the full layout (experimental).

- Set your virtual instruments' pitch bend range to double the LinnStrument's value.

## How to Play

### Layout

Each row consists of a whole tone scale, separated by 4ths, which cause the rows to alternate.  It sounds strange at first but because of the layout's relation to the circle of 5ths, it makes a number of things easier to play and remember than the default chromatic layout.

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

## Basic Chord Shapes

The symbol 'o' is used for a pressed note to show the shape:

```
Major:
 o
o o

Minor:
o o
 o

Dim:
o
 o
  o
  
Aug:
o o o

Sus2:
 o
oo

Sus4:
oo
o
 
Maj7:
 o o
o o

m7:
 o
o o
 o
 
7:
o
 o
o o
```

## Circle of 5ths

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

## Visualizer

### DAW visualization

Using this program, you can visualize the midi playing in your DAW on both the screen and LinnStrument.
You do this by creating another device in LoopMidi called "visualizer" then use a Midi Out plugin
on the track you want to visualize and set the plugin to use the visualizer midi device.

### Synthesia

To use the visualizer with Synthesia, create a new MIDI loopback device called "visualizer".
In Synthesia settings, set it as an output device for note lights.

## Full MPE

### 128 Key

To use ChPerNote/MPE mode, set your LinnStrument 128 to "NO OVERLAP" with a transposition of -3 octaves and +6 pitch.
Then, set `no_overlap=true` in your settings.ini file (if you don't have one, copy it from settings.ini.example).

### 200 Key

Note: This workaround has not been tested on the 200 but it should work.

To use ChPerNote/MPE mode, first enable SPLIT.  Then, set your LinnStrument to "NO OVERLAP" with a transposition on both splits of -3 octaves and +6 pitch.  Make sure ChPerNote mode is also set on both splits.
Then, set `no_overlap=true` and `hardware_split=true` in your settings.ini file (if you don't have one, copy it from settings.ini.example).

## Split

Because of the diagonal nature of the layout, the split is diagonal as well (through G# in the center).
To use a split, create another midi loopback port called "split" and set `split=true` in your settings.ini.
At the moment this requires using full MPE mode to work (see section `Full MPE`).
The split creates a second virtual instrument you can access in your DAW called "split".

Note: If you use the 128, do not set the split on your linnstrument.  The program will make its own split.
However, if you use the 200, you will need to enable to split in order to have all the notes come through.
(This is to work around a limitation with no overlap mode.)

## Pitch Bend

To get pitch bending working properly, you'll need to set your virtual instruments' pitch bend range to exactly double the amount of the LinnStrument's range.

## Future Plans

- Scale integration
- Touchscreen support
- Find a way to adjust vibrato sensitivity without affecting slides.  Roger Linn has indicated that this is probably impossible, but I have a few ideas to try.
- Better velocity curve settings (right now its only basic options in the settings.ini).
- Better GUI and integration with the settings file.

## Contact / Questions

I'm on the LinnStrument Discord at https://discord.gg/h2BcrzmTXe.  Come hang out!
