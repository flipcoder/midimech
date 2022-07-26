# linnstrument-wholetone

"Alternating Whole-tone" layout and visualizer for the Linnstrument.  I've always considered this the easiest musical layout possible, and once you learn the chords and scales you'll understand why.

This program is a work-in-progress so some things are only partially working.

License: MIT

![Screenshot](https://i.imgur.com/F0VQU4F.png)

## Setup

- First create a virtual midi device with LoopMidi.  Then set your DAW to use loopmidi instead of the linnstrument.  Make sure the virtual device you set up has "loopmidi" in its device name, since this is how its detected by the program.

- Set your LinnStrument to use ChPerRow mode.

- Download the project by typing the following commands in terminal:
```
git clone https://github.com/flipcoder/linnstrument-wholetone
```

- Switch to the new project folder:
```
cd linnstrument-wholetone
```

- Install the dependencies:
```
pip install -r requirements.txt
```

- Run app.py.  You should see a window pop up with the layout.

- If this works, your linnstrument will show the colors of the wholetone layout and be playable in your DAW.

## Playing Scales

The major/minor scales are shaped with the "3-4" pattern.  3 notes on first row, then 4 notes on next row, then repeat moving over 1 space, making runs fit across the fingers easily.
Here's what it looks like:

```
4567
123
```

All the modes for this, (such as lydian, dorian, etc.) are accessible by picking a different starting note.

Similarly, the pentatonic scale modes fit the "2-3" pattern:

```
345
12
```

Melodic minor has a "2-5" pattern:

```
34567
 12
```

You may notice that based on your starting note, the further left you go, the brighter the scale, and the further right,
the darker the scale.  This is because the alternating whole tone layout resembles a staggered circle of 5ths which corresponds with musical brightness.

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

Another interesting thing about this layout on the Linnstrument is you can walk up and down the major and minor 3rd intervals within a scale without lifting your fingers.
This technique is most useful for a piano sound or something where pitch shifting is disabled.

So there's a quick rundown.  There's a lot more fun shapes to learn but this will get you started.  Hope you enjoy!

## Visualizer

Using this program, you can visualize the midi playing in your DAW on both the screen and LinnStrument.
You do this by creating another device in LoopMidi called "visualizer" then use a Midi Out plugin
on the track you want to visualize and set the plugin to use the visualizer midi device.

