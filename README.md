# linnstrument-wholetone
[WORK IN PROGRESS] An alternate tuning system and visualizer for the Linnstrument

Instructions:

First create a virtual midi device with LoopMidi.  Then set your DAW to use loopmidi instead of the linnstrument.

Set your LinnStrument to use ChPerRow mode.

You'll need python3 installed.  Get the python dependencies by running this in terminal in the program's directory:

```
pip install -r requirements.txt
```

Then run app.py.  You should see a window pop up with the layout and a console window possibly displaying errors.

The visualizer, chord analyzer, and pitch bend are not done yet, but I'll be updating this soon.

If this works, your linnstrument will show the colors of the wholetone layout and be playable in your DAW.
