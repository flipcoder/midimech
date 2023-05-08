#!/usr/bin/python3
# from tkinter import *
from collections import OrderedDict
from configparser import ConfigParser
import os, sys, glm, copy, binascii, struct, math, traceback, signal
import rtmidi2
from dataclasses import dataclass
from glm import ivec2, vec2, ivec3, vec3
import time

from src.util import *
from src.constants import *
from src.options import Options
from src.note import Note
from src.settings import DeviceSettings
from src.core import Core

with open(os.devnull, "w") as devnull:
    # suppress pygame messages
    stdout = sys.stdout
    sys.stdout = devnull
    import pygame, pygame.midi, pygame.gfxdraw

    sys.stdout = stdout
import pygame_gui

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


DEFAULT_OPTIONS = Options()


def main():
    core = None
    try:
        core = Core()
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
