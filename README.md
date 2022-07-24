# linnstrument-wholetone

An interleaved wholetone tuning system and visualizer for the Linnstrument.

This is still a work-in-progress so some things are only partially working.

License: MIT

![Screenshot](https://i.imgur.com/NX34ddB.png)

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

## Visualizer

You can visualize midi input from your DAW back onto the screen to figure out how to play certain parts.
You do this by creating another device in LoopMidi called "visualizer" then use a Midi Out plugin
on the track you want to visualize and set the plugin to use the visualizer virtual midi device.

This mode only visualizes on the screen for now, but I'll eventually have it set the lights on the instrument as well.

## Chord Anazlyer

There is a very basic chord analyzer but its disabled by default to improve latency.  You can enable it by
setting `CHORD_ANALYZER = True` in the app.py file.

