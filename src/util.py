import os, sys, glm, copy, binascii, struct, math, traceback
from dataclasses import dataclass
import glm
from src.constants import *

# suppress pygame messages to keep console output clean
with open(os.devnull, "w") as devnull:
    stdout = sys.stdout
    sys.stdout = devnull
    import pygame, pygame.midi, pygame.gfxdraw

    sys.stdout = stdout
import pygame_gui

# import mido
from collections import OrderedDict
from configparser import ConfigParser

try:
    import webcolors
except ImportError:
    error("The project dependencies have changed! Run the requirements setup command again!")

def error(msg):
    print(msg)
    sys.exit(1)

def sign(val):
    tv = type(val)
    if tv is int:
        if val > 0:
            return 1
        elif val == 0:
            return 0
        else:
            return -1
    elif tv is float:
        if val >= EPSILON:
            return 1.0
        elif abs(val) < EPSILON:
            return 0.0
        else:
            return -1.0
    assert False


def clamp(low, high, val):
    return max(low, min(val, high))


class Object:
    def __init__(self, **kwargs):
        self.game = kwargs.get("game", None)
        self.attached = False
        if self.game:
            self.game.world.attach(self)

        self.pos = glm.vec2(*kwargs.get("pos", (0.0, 0.0)))
        self.vel = glm.vec2(*kwargs.get("vel", (0.0, 0.0)))
        self.sz = glm.vec2(*kwargs.get("sz", (0.0, 0.0)))
        self.surface = kwargs.get("surface", None)


class Screen(Object):
    def __init__(self, core, screen):
        self.core = core
        self.pos = glm.vec2(0.0, 0.0)
        self.sz = glm.vec2(core.screen_w, core.screen_h)
        self.surface = pygame.Surface(core.screen_sz).convert()
        self.screen = screen

    def render(self):
        self.screen.blit(self.surface, (0, 0))


def nothing():
    pass


def get_option(section, option, default):
    if section is None:
        return default
    typ = type(default)
    if typ is bool:
        return section.get(option, "true" if default else "false").lower() in [
            "true",
            "yes",
            "on",
        ]
    if typ is int:
        return int(section.get(option, default))
    if typ is float:
        return float(section.get(option, default))
    if typ is str:
        return section.get(option, default)
    print("Invalid option value for", option)

# def invert_color(col): # ivec 255
#     r = vec3(col) / 255.0
#     for i in range(3):
#         r[i] = 1.0 - r[i]
#         r[i] *= 255
#     return ivec3(r)

def decompose_pitch_bend(pitch_bend_bytes):
    pitch_bend_value = (pitch_bend_bytes[1] << 7) + pitch_bend_bytes[0]
    pitch_bend_norm = (pitch_bend_value - 8192) / 8192.0
    return pitch_bend_norm

def compose_pitch_bend(pitch_bend_norm):
    pitch_bend_value = int((pitch_bend_norm + 1.0) * 8192)
    pitch_bend_bytes = [pitch_bend_value & 0x7F, (pitch_bend_value >> 7) & 0x7F]
    return pitch_bend_bytes

def decode_value(value):
    lsb = value & 0x7F
    msb = (value >> 7) & 0x7F
    return msb, lsb

# def pitch_bend_to_semitones(pitch_bend_value):
#     return bend_semitones

def get_color(col):
    if col.startswith("#"):
        return webcolors.hex_to_rgb(col)
    return webcolors.name_to_rgb(col)
