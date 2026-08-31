#!/usr/bin/python3
# from tkinter import *
from collections import OrderedDict
from configparser import ConfigParser
import os, sys, glm, copy, binascii, struct, math, traceback, signal
import rtmidi2
from dataclasses import dataclass
from glm import ivec2, vec2, ivec3, vec3
import time

from src.core import Core

# suppress pygame messages to keep console clean
with open(os.devnull, "w") as devnull:
    stdout = sys.stdout
    sys.stdout = devnull
    import pygame, pygame.midi, pygame.gfxdraw

    sys.stdout = stdout
import pygame_gui

# pymsgbox crashes on Mac, so we can't use this right now
# try:
#     import pymsgbox
# except ImportError:
#     print("The project dependencies have changed! Run the requirements setup command again!")
#     sys.exit(1)

try:
    import launchpad_py as launchpad
except ImportError:
    try:
        import launchpad
    except ImportError:
        error("The project dependencies have changed! Run the requirements setup command again!")

try:
    import yaml
except ImportError:
    error("The project dependencies have changed! Run the requirements setup command again!")

# import mido

try:
    import musicpy as mp
except ImportError:
    error("The project dependencies have changed! Run the requirements setup command again!")


def main():
    core = None
    try:
        core = Core()
        original_midi_write = core.midi_write
        def patched_midi_write(out, msg):
            try:
                if (
                    msg
                    and len(msg) >= 3
                    and (msg[0] & 0xF0) == 0xB0
                    and getattr(core, "split", core.options.split)
                    and core.options.one_channel == 0
                ):
                    split_out = getattr(core, "split_out", None)
                    if (
                        split_out is not None
                        and split_out is not out
                        and out is getattr(core, "midi_out", None)
                        and (msg[0] & 0x0F)
                        >= getattr(core, "split_channel", getattr(core, "width", 16) // 2)
                    ):
                        out = split_out
            except Exception:
                pass
            original_midi_write(out, msg)
        core.midi_write = patched_midi_write
        core()
    except SystemExit:
        pass
    except:
        print(traceback.format_exc())
    del core
    pygame.midi.quit()
    pygame.display.quit()
    os._exit(0)
    # pygame.quit()


if __name__ == "__main__":
    main()
