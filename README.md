# linnstrument-wholetone

An interleaved wholetone tuning system and visualizer for the Linnstrument.

This is still a work-in-progress so some things are only partially working or completely broken.  It currently only works for the 128, but if I get a tester who has the bigger one I can try to make it work.

License: MIT

![Screenshot](https://i.imgur.com/NX34ddB.png)

## Setup

- First create a virtual midi device with LoopMidi.  Then set your DAW to use loopmidi instead of the linnstrument.

- Set your LinnStrument to use ChPerRow mode.

- Install python3, then install the dependencies.  Get the dependencies by running this in terminal in the program's directory:

```
pip install -r requirements.txt
```

- Run app.py.  You should see a window pop up with the layout.

- If this works, your linnstrument will show the colors of the wholetone layout and be playable in your DAW.

## Visualizer

You can visualize midi input from your DAW back onto the screen to figure out how to play certain parts.
You do this by creating another device in LoopMidi called "visualizer" then use a Midi Out plugin
on the track you want to visualize and set the plugin to use the visualizer virtual midi device.

This mode only visualizes on the screen for now, but I'll eventually have it set the lights on the instrument as well.

## Chord Anazlyer

There is a very basic chord analyzer but its disabled by default to improve latency.  You can enable it by
setting `CHORD_ANALYZER = True` in the app.py file.
