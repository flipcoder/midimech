#!/usr/bin/python3
# from tkinter import *
import os,sys,glm,copy,binascii,struct,math,traceback
import rtmidi2
from util import *
from dataclasses import dataclass
import glm

with open(os.devnull, 'w') as devnull:
    # suppress pygame messages
    stdout = sys.stdout
    sys.stdout = devnull
    import pygame, pygame.midi, pygame.gfxdraw
    sys.stdout = stdout
import pygame_gui
# import mido
from collections import OrderedDict
from configparser import ConfigParser

TITLE = "Wholetone Layout"
# FOCUS = False
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
WHOLETONE = True
FONT_SZ = 32
BRIGHTNESS = 0.4
C_COLOR = glm.ivec3(0,128 * BRIGHTNESS,0)
YELLOW = glm.ivec3(205 * BRIGHTNESS,127 * BRIGHTNESS,0)
LIGHT = glm.ivec3(0,0,128 * BRIGHTNESS)
FGAB = glm.ivec3(64 * BRIGHTNESS)
GRAY = glm.ivec3(16 * BRIGHTNESS)
BORDER_COLOR = glm.ivec3(48)
DARK = glm.ivec3(0)
BASE_OFFSET = -4
# CHORD_ANALYZER = get_option(opts,'chord_analyzer',False)
EPSILON = 0.0001
FADE_SPEED = 4.0

b = 0.5
COLOR_CODES = [
    glm.ivec3(0), # default color
    glm.ivec3(255, 0, 0), # red
    glm.ivec3(205, 127, 0), # yellow
    glm.ivec3(0, 127, 0), # green
    glm.ivec3(0, 127, 127), # cyan
    glm.ivec3(0, 0, 128), # blue
    glm.ivec3(255, 0, 255), # magenta
    glm.ivec3(0), # off
    glm.ivec3(80,80,80), # gray
    glm.ivec3(255,127,0), # orange
    glm.ivec3(0,255,0), # lime
    glm.ivec3(255,127,127), # pink
]

# NOTE_COLORS = [
#     glm.ivec3(255, 0, 0), # C
#     glm.ivec3(255/2, 0, 0), # C#
#     glm.ivec3(255, 127, 0), # D
#     glm.ivec3(255/2, 127/2, 0), # D#
#     glm.ivec3(255, 255, 0), # E
#     glm.ivec3(0, 255, 0), # F
#     glm.ivec3(0, 255/2, 0), # F#
#     glm.ivec3(0, 0, 255), # G
#     glm.ivec3(0, 0, 255/2), # G#
#     glm.ivec3(128, 0, 128), # A
#     glm.ivec3(128/2, 0, 128/2), # A#
#     glm.ivec3(255, 0, 255) # B
# ]

# def invert_color(col): # ivec 255
#     r = glm.vec3(col) / 255.0
#     for i in range(3):
#         r[i] = 1.0 - r[i]
#         r[i] *= 255
#     return glm.ivec3(r)

class Note:
    def __init__(self):
        self.bend = 0.0
        self.pressed = False
        self.intensity = 0.0 # how much to light marker up
        self.pressure = 0.0 # how much the note is being pressed
        self.dirty = False
        self.location: glm.ivec2 = None # on board
    def logic(self, dt):
        if self.pressed: # pressed, fade to pressure value
            if self.intensity != self.pressure:
                self.dirty = True
                if self.intensity < self.pressure:
                    self.intensity = min(pressure, self.intensity + dt * FADE_SPEED)
                else:
                    self.intensity = max(pressure, self.intensity - dt * FADE_SPEED)
        else: # not pressed, fade out
            if self.intensity > 0.0:
                self.dirty = True
                self.pressure  = 0.0
                self.intensity = max(0.0, self.intensity - dt * FADE_SPEED)

@dataclass
class Options:
    pass

class Core:

    def init_hardware(self):
        pass
    
    def has_velocity_curve(self):
        return abs(self.velocity_curve_ - 1.0) > EPSILON

    def has_velocity_settings(self):
        return self.options.min_velocity > 0 or self.options.max_velocity < 127 or self.has_velocity_curve()

    def velocity_curve(self, val): # 0-1
        if self.has_velocity_curve():
            val = val**self.velocity_curve_
        return val
    
    def send_cc(self, channel, cc, val):
        if not self.linn_out:
            return
        # msg = [0xb0 | channel, cc, val]
        self.linn_out.send_cc(channel, cc, val)
        # self.linn_out.send_messages(0xb0, [(channel, cc, val)])

    def set_light(self, x, y, col): # col is [1,11], 0 resets

        if y < 0 or y > self.board_h:
            return
        if x < 0 or x > self.board_w:
            return
        
        self.red_lights[y][x] = (col==1)
        self.send_cc(0, 20, x+1)
        self.send_cc(0, 21, self.board_h - y - 1)
        # if self.options.lights:
        self.send_cc(0, 22, col)
        # else:
        #     self.send_cc(0, 22, 7) # no light

    def reset_light(self, x, y):
        if not self.options.lights: return
        note = self.get_note_index(x, y) % 12
        light_col = self.options.lights[note]
        self.set_light(x, y, light_col)
        self.red_lights[y][x] = False
    
    def setup_lights(self):
        for y in range(self.board_h):
            for x in range(self.board_w):
                if self.red_lights[y][x]:
                    self.set_light(x, y, 1)
                else:
                    self.reset_light(x, y)
    

    def reset_lights(self):
        for y in range(self.board_h):
            for x in range(self.board_w):
                self.set_light(x, y, 0)
    
    def get_octave(self, x, y):
        return self.octaves[y - self.board_h + self.flipped][x] + self.octave

    def xy_to_midi(self, x, y):
        row = self.board_h - y
        r = x % self.board_w + 25.5 + 2.5 * row # FIXME: make this simpler
        r *= 2
        r = int(r)
        r += (self.octave + self.octave_base) * 12
        r += self.transpose*2
        if self.flipped:
            r += 7
        return r

    def get_note_index(self, x, y):
        y += self.flipped
        x += self.transpose
        ofs = (self.board_h - y) // 2 + BASE_OFFSET
        step = 2 if WHOLETONE else 1
        if y%2 == 1:
            return ((x-ofs)*step)%len(NOTES)
        else:
            return ((x-ofs)*step+7)%len(NOTES)

    def get_note(self, x, y):
        return NOTES[self.get_note_index(x, y)]

    def get_color(self, x, y):
        # return NOTE_COLORS[get_note_index(x, y)]
        note = self.get_note_index(x, y)
        return COLOR_CODES[self.options.lights[note]]

    def mouse_held(self):
        return self.mouse_midi != -1

    def mouse_press(self, x, y, state=True, hold=False):
        if y < 0:
            return
        
        # if we're not intending to hold the note, we release the previous primary note
        if not hold:
            if self.mouse_held():
                self.mouse_release()
        
        vel = y % int(self.button_sz)
        x /= int(self.button_sz)
        y /= int(self.button_sz)
        
        vel = vel / int(self.button_sz)
        vel = 1 - vel
        vel *= 127
        vel = clamp(0, 127, int(vel))
        
        x, y = int(x), int(y)
        
        self.mark_xy(x, y, state)
        v = glm.ivec2(x, y)
        midinote = self.xy_to_midi(v.x, v.y)
        if not hold:
            self.mouse_mark = v
            self.mouse_midi = midinote
        data = [0x90 if state else 0x80, midinote, vel]
        if self.midi_out:
            self.midi_write(self.midi_out, data, 0)

    def mouse_hold(self, x, y):
        return self.mouse_press(x, y, True, hold=True)

    def mouse_release(self, x=None, y=None):
        # x and y provided? it's a specific coordinate
        if x is not None and y is not None:
            return self.mouse_press(x, y, False)
        # x and y not provided? it uses the primary mouse coordinate
        if self.mouse_midi != -1:
            self.mark_xy(self.mouse_mark.x, self.mouse_mark.y, False)
            data = [0x80, self.mouse_midi, 127]
            if self.midi_out:
                self.midi_write(self.midi_out, data, 0)
            self.mouse_midi = -1

    # Given an x,y position, find the octave
    #  (used to initialize octaves 2D array)
    def init_octave(self, x, y):
        return int((x+4+self.transpose+y*2.5)//6)
    
    def init_board(self):
        # self.octaves = [
        #     # 200 size ---------------------------------------------------------------v
        #     # 128 size ------------------------------------v
        #     [3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7],
        #     [3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 7, 7],
        #     [2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6],
        #     [2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6],
        #     [1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5],
        #     [1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5],
        #     [1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5],
        #     [0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4]
        # ]
        # generate grid of octaves like above
        self.octaves = []
        for y in range(self.board_h + 1): # 1 = flipping
            self.octaves.append([])
            for x in range(self.max_width):
                self.octaves[y].append(self.init_octave(x, y))
        self.octaves = list(reversed(self.octaves))

        self.notes = [None] * 16 # polyphony
        for i in range(len(self.notes)):
            self.notes[i] = Note()

    def midi_write(self, dev, msg, ts=0):
        if dev:
            dev.send_raw(*msg)

    def cb_midi_in(self, data, ts):
        # print(data, ts)
        d0 = data[0]
        ch = d0 & 0x0f
        msg = (data[0] & 0xf0) >> 4
        if self.options.one_channel:
            data[0] = d0 & 0xf0 # send all to channel 0 if enabled
        row = None
        if not self.options.no_overlap:
            row = ch % 8
            col = ch // 8
        width = self.board_w//2 if self.options.hardware_split else self.board_w
        if msg == 9: # note on
            if self.options.no_overlap:
                row = data[1] // width
                col = data[1] % width
                data[1] = data[1] % width + 30 + 2.5*row
                data[1] *= 2
                data[1] = int(data[1])
                if self.options.hardware_split and ch >= 8:
                    data[1] += width * 2
            else:
                data[1] *= 2
                try:
                    data[1] -= row * 5
                except IndexError:
                    pass
            
            data[1] += (self.octave + self.octave_base) * 12
            data[1] += BASE_OFFSET
            midinote = data[1] - 24 + self.transpose*2
            if self.is_split():
                split_chan = self.channel_from_split(row, col)
            self.mark(midinote, 1, only_row=row)
            data[1] += self.out_octave * 12 + self.transpose*2
            if self.flipped:
                data[1] += 7
            
            # apply velocity curve
            vel = data[2]/127
            if self.has_velocity_settings():
                vel = self.velocity_curve(data[2]/127)
                data[2] = clamp(self.options.min_velocity,self.options.max_velocity,int(vel*127+0.5))

            note = self.notes[ch]
            if note.location is None:
                note.location = glm.ivec2(0)
            self.notes[ch].location.x = col
            self.notes[ch].location.y = row
            self.notes[ch].pressure = vel
            
            if self.is_split():
                if split_chan == 0:
                    # self.midi_out.write([[data, ev[1]]]
                    self.midi_write(self.midi_out, data, ts)
                else:
                    self.midi_write(self.split_out, data, ts)
            else:
                self.midi_write(self.midi_out, data, ts)
            
            # print('note on: ', data)
        elif msg == 8: # note off
            if self.options.no_overlap:
                row = data[1] // width
                col = data[1] % width
                data[1] = data[1] % width + 30 + 2.5*row
                data[1] *= 2
                data[1] = int(data[1])
                if self.options.hardware_split and ch >= 8:
                    data[1] += width * 2
            else:
                data[1] *= 2
                try:
                    data[1] -= row * 5
                except IndexError:
                    pass
            
            data[1] += (self.octave + self.octave_base) * 12
            data[1] += BASE_OFFSET
            midinote = data[1] - 24 + self.transpose*2
            if self.is_split():
                split_chan = self.channel_from_split(row, col)
            self.mark(midinote, 0, only_row=row)
            data[1] += self.out_octave * 12 + self.transpose*2
            if self.flipped:
                data[1] += 7
        
            if self.is_split():
                if split_chan == 0:
                    self.midi_write(self.midi_out, data, ts)
                else:
                    self.midi_write(self.split_out, data, ts)
            else:
                self.midi_write(self.midi_out, data, ts)
            # print('note off: ', data)
        elif 0xf0 <= msg <= 0xf7: # sysex
            self.midi_write(self.midi_out, data, ts)
        else:
            # control change, aftertouch, pitch bend, etc...
            if data[1] == 64: # sustain pedal
                if self.is_split():
                    for dev in self.sustainable_devices():
                        self.midi_write(dev, data, ts)
                else:
                    self.midi_write(self.midi_out, data, ts)
            elif self.is_split():
                note = self.notes[ch]
                if ch == 0:
                    self.midi_write(self.midi_out, data, ts)
                    self.midi_write(self.split_out, data, ts)
                elif note.location is not None:
                    col = self.notes[ch].location.x
                    row = self.notes[ch].location.y
                    split_chan = self.channel_from_split(row, col)
                    if split_chan:
                        self.midi_write(self.split_out, data, ts)
                    else:
                        self.midi_write(self.midi_out, data, ts)
                else:
                    self.midi_write(self.midi_out, data, ts)
                    self.midi_write(self.split_out, data, ts)
            else:
                self.midi_write(self.midi_out, data, ts)
        
    def cb_visualizer(self, data, ts):
        # print(msg, ts)
        ch = data[0] & 0x0f
        msg = data[0] >> 4
        if msg == 9: # note on
            self.mark(data[1] + self.vis_octave*12, 1, True)
        elif msg == 8: # note off
            self.mark(data[1] + self.vis_octave*12, 0, True)

    def cb_foot(self, data, ts):
        ch = data[0] & 0x0f
        msg = (data[0] & 0xf0) >> 4
        if msg == 11:
            # change velocity curve
            val = data[1]
            val2 = None
            if val == 27: # left expr pedal
                self.midi_write(self.midi_out, data, 0)
                if self.is_split():
                    data[1] = 67 # soft pedal
                    self.midi_write(self.split_out, data, 0)
            elif val == 7: # right expr pedal
                val2 = 1.0 - data[2] / 127
                low = self.options.velocity_curve_LOW
                high = self.options.velocity_curve_HIGH
                self.velocity_curve_ = low + val2*(high-low)

    def save():
        self.cfg = ConfigParser(allow_no_value=True)
        general = self.cfg['general'] = {}
        if self.options.lights:
            general['lights'] = ','.join(map(str,self.options.lights))
        general['one_channel'] = self.options.one_channel
        general['velocity_curve'] = self.options.velocity_curve
        general['min_velocity'] = self.options.min_velocity
        general['max_velocity'] = self.options.max_velocity
        general['no_overlap'] = self.options.no_overlap
        general['hardware_split'] = self.options.hardware_split
        general['show_lowest_note'] = self.options.show_lowest_note
        general['midi_out'] = self.options.midi_out
        general['split_out'] = self.options.split_out
        general['split'] = SPLIT
        general['fps'] = self.options.fps
        general['sustain'] = SUSTAIN
        self.cfg['general'] = general
        with open('settings_temp.ini', 'w') as configfile:
            self.cfg.write(configfile)
    
    def __init__(self):

        self.cfg = ConfigParser(allow_no_value=True)
        self.cfg.read('settings.ini')
        try:
            opts = self.cfg['general']
        except KeyError:
            opts = None

        self.options = Options()

        default_lights = '4,7,3,7,3,3,7,3,7,3,7,3'
        
        # LIGHT = glm.ivec3(127)
        self.options.lights = get_option(opts,'lights',default_lights)
        if self.options.lights:
            self.options.lights = list(map(lambda x: int(x), self.options.lights.split(',')))
        self.options.one_channel = get_option(opts,'one_channel',False)
        
        # bend the velocity curve, examples: 0.5=sqrt, 1.0=default, 2.0=squared
        self.options.velocity_curve = get_option(opts,'velocity_curve',1.0)

        # these settings are only used with the foot controller
        self.options.velocity_curve_low = get_option(opts,'velocity_curve_low',0.5) # loudest (!)
        self.options.velocity_curve_high = get_option(opts,'velocity_curve_high',3.0) # quietest (!)

        if self.options.velocity_curve < EPSILON: # if its near zero, set default
            self.options.velocity_curve = 1.0 # default
        
        self.options.min_velocity = get_option(opts,'min_velocity',0)
        self.options.max_velocity = get_option(opts,'max_velocity',127)
        self.options.show_lowest_note = get_option(opts,'show_lowest_note',False)
        self.options.no_overlap = get_option(opts,'no_overlap',False)
        self.options.hardware_split = get_option(opts,'hardware_split',False)
        self.options.midi_out = get_option(opts,'midi_out','loopmidi')
        self.options.split_out = get_option(opts,'split_out','split')
        self.options.fps = get_option(opts,'fps',60)
        self.split_state = self.options.split = get_option(opts,'split',False)
        self.options.foot_in = get_option(opts,'foot_in','')
        self.options.sustain = get_option(opts,'sustain',1.0) # sustain scale

        # which split the sustain affects
        self.options.sustain_split = get_option(opts, 'sustain_split', 'both') # left, right, both
        if self.options.sustain_split not in ('left', 'right', 'both'):
            print("Invalid sustain split value. Options: left, right, both.")
            sys.exit(1)

        # simulator keys
        self.keys = {}
        i = 0
        for key in '1234567890-=':
            self.keys[ord(key)] = 62 + i
            i += 2
        self.keys[pygame.K_BACKSPACE] = 62 + i
        i = 0
        for key in 'qwertyuiop[]\\':
            self.keys[ord(key)] = 57 + i
            i += 2
        i = 0
        for key in 'asdfghjkl;\'':
            self.keys[ord(key)] = 52 + i
            i += 2
        self.keys[pygame.K_RETURN] = 52 + i
        i = 0
        for key in 'zxcvbnm,./':
            self.keys[ord(key)] = 47 + i
            i += 2
        self.keys[pygame.K_RSHIFT] = 47 + i

        # self.panel = CHORD_ANALYZER
        self.menu_sz = 32 # 64
        self.max_width = 25 # MAX WIDTH OF LINNSTRUMENT
        self.board_h = 8
        self.scale = glm.vec2(64.0)
        
        self.board_w = 16
        self.board_sz = glm.ivec2(self.board_w, self.board_h)
        self.screen_w = self.board_w * self.scale.x
        self.screen_h = self.board_h * self.scale.y + self.menu_sz
        self.button_sz = self.screen_w / self.board_w
        self.screen_sz = glm.ivec2(self.screen_w, self.screen_h)
        
        self.lowest_note = None # x,y location of lowest note currently pressed
        self.lowest_note_midi = None # midi number of lowest note currently pressed
        self.octave = 0
        self.out_octave = 0
        self.vis_octave = -2 # this is for both the visualizer and the keyboard simulator marking atm
        self.octave_base = -2
        self.transpose = 0
        self.rotated = False # transpose -3 whole steps
        self.flipped = False # vertically shift +1
        self.config_save_timer = 1.0

        self.velocity_curve_ = self.options.velocity_curve

        self.mouse_mark = glm.ivec2(0)
        self.mouse_midi = -1

        self.init_board()

        # load midi file from command line (playiung it is not yet impl)
        # self.midi_in_fn = None
        # self.midifile = None
        # if len(sys.argv) > 1:
        #     self.midi_in_fn = sys.argv[1]
        #     if self.midi_in_fn.to_lower().endswith('.mid'):
        #         self.midifile = mido.MidiFile(midi_fn)
        
        # self.root = Tk()
        # self.menubar = Menu(self.root)
        # self.filemenu = Menu(self.menubar, tearoff=0)
        # self.filemenu.add_command(label="Open", command=nothing)
        # self.root.config(menu=self.menubar)
        # self.embed = Frame(self.root, width=self.screen_w, height=self.screen_h)
        # self.embed.pack()
        # os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
        # self.root.update()
        # self.menubar.add_cascade(label="File", menu=self.filemenu)
        # self.root.protocol("WM_DELETE_WINDOW", self.quit)
        pygame.init()
        pygame.display.set_caption(TITLE)
        # if FOCUS:
        #     pygame.mouse.set_visible(0)
        #     pygame.event.set_grab(True)
        self.screen = Screen(self,pygame.display.set_mode(self.screen_sz,pygame.DOUBLEBUF))
        
        bs = glm.ivec2(self.button_sz,self.menu_sz) # // 2
        self.gui = pygame_gui.UIManager(self.screen_sz)
        y = 0
        self.btn_octave_down = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((2,y),bs),
            text='<OCT',
            manager=self.gui
        )
        self.btn_octave_up = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((bs.x+2,y),bs),
            text='OCT>',
            manager=self.gui
        )
        self.btn_transpose_down = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((bs.x*2+2,y),bs),
            text='<TR',
            manager=self.gui
        )
        self.btn_transpose_up = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((bs.x*3+2,y),bs),
            text='TR>',
            manager=self.gui
        )
        self.btn_size = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((bs.x*4+2,y),bs),
            text='SIZE',
            manager=self.gui
        )
        self.btn_rotate = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((bs.x*5+2,y),bs),
            text='ROT',
            manager=self.gui
        )
        self.btn_flip = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((bs.x*6+2,y),bs),
            text='FLIP',
            manager=self.gui
        )
        
        if self.options.no_overlap: # split only works with no overlap for now
            self.btn_split = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((bs.x*7+2,y),(bs.x*2,bs.y)),
                text='SPLIT: ' + ('ON' if self.split_state else 'OFF'),
                manager=self.gui
            )

        # self.slider_label = pygame_gui.elements.UILabel(
        #     relative_rect=pygame.Rect((0,y+bs.y),(bs.x*2,bs.y)),
        #     text='Velocity Curve',
        #     manager=self.gui
        # )
        # self.slider_velocity = pygame_gui.elements.UIHorizontalSlider (
        #     relative_rect=pygame.Rect((bs.x*2+2,y+bs.y),(bs.x*2,bs.y)),
        #     start_value=self.options.velocity_curve,
        #     value_range=[0,1],
        #     manager=self.gui
        # )
        
        # pygame.midi.init()
        
        self.out = []
        self.midi_in = None
        ins = []
        outs = []
        # in_devs = [
        #     'linnstrument',
        #     'visualizer'
        # ]
        # out_devs = [
        #     'linnstrument',
        #     self.options.midi_out,
        #     'loopmidi'
        # ]
        # for i in range(pygame.midi.get_count()):
        #     info = pygame.midi.get_device_info(i)
        #     # print(info)
        #     if info[2]==1:
        #         ins.append((i,str(info[1])))
        #     if info[3]==1:
        #         outs.append((i,str(info[1])))

        # innames = []
        # for inx in ins:
        #     innames += [str(inx[1])]
        #     print('in: ', inx)

        self.linn_out = None
        self.midi_out = None
        self.split_out = None

        outnames = rtmidi2.get_out_ports()
        for i in range(len(outnames)):
            name = outnames[i]
            name_lower = name.lower()
            # print(name_lower)
            if "linnstrument" in name_lower:
                print("LinnStrument (Out): " + name)
                self.linn_out = rtmidi2.MidiOut()
                self.linn_out.open_port(i)
            elif self.options.split_out and self.options.split_out in name_lower:
                print("Split (Out): " + name)
                self.split_out = rtmidi2.MidiOut()
                self.split_out.open_port(i)
            elif self.options.midi_out in name_lower:
                print("Loopback (Out): " + name)
                self.midi_out = rtmidi2.MidiOut()
                self.midi_out.open_port(i)

        if not self.linn_out:
            print("No LinnStrument output device detected. (Can't control lights)")
        if not self.midi_out:
            print("No MIDI output device detected. (Did you install a midi loopback device?)")

        self.midi_in = None
        self.visualizer = None

        innames = rtmidi2.get_in_ports()
        for i in range(len(innames)):
            name = innames[i]
            name_lower = name.lower()
            if "visualizer" in name_lower:
                print("Visualizer (In): " + name)
                self.visualizer = rtmidi2.MidiIn()
                self.visualizer.callback = self.cb_visualizer
                self.visualizer.open_port(i)
            elif "linnstrument" in name_lower:
                print("LinnStrument (In): " + name)
                self.midi_in = rtmidi2.MidiIn()
                self.midi_in.callback = self.cb_midi_in
                self.midi_in.open_port(i)
            elif self.options.foot_in and self.options.foot_in in name_lower:
                print("Foot Controller (In): " + name)
                self.foot_in = rtmidi2.MidiIn()
                self.foot_in.open_port(i)
                self.foot_in.callback = self.cb_foot
        
        self.done = False
        
        self.dirty = True
        self.dirty_lights = True
            
        w = self.max_width
        h = self.board_h
        self.board = [[0 for x in range(w)] for y in range(h)]
        self.red_lights = [[False for x in range(w)] for y in range(h)]

        self.font = pygame.font.Font(None, FONT_SZ)
            
        # self.retro_font = pygame.font.Font("PressStart2P.ttf", FONT_SZ)
        self.clock = pygame.time.Clock()

        self.init_hardware()

        # self.setup_lights()

    def transpose_board(self, val):
        aval = abs(val)
        if aval > 1: # more than one shift
            sval = sign(val)
            for rpt in range(aval):
                self.transpose_board(sval)
                self.tranpose += sval
        elif val==1: # shift right (add column left)
            for y in range(len(self.board)):
                self.board[y] = [0] + self.board[y][:-1]
            self.transpose += val
        elif val==-1: # shift left (add column right)
            for y in range(len(self.board)):
                self.board[y] = self.board[y][1:] + [0]
            self.transpose += val

    def quit(self):
        self.reset_lights()
        self.done = True

    def clear_marks(self, use_lights=False):
        for row in rows:
            x = 0
            for x in range(len(row)):
                idx = self.get_note_index(x, y)
                try:
                    self.board[y+self.flipped][x] = state
                except IndexError:
                    print("clear_marks: Out of range")
                    pass
                if use_lights:
                    if state:
                        self.set_light(x, y, 1)
                    else:
                        self.reset_light(x, y)
            y += 1
        self.dirty = True

    def mark_xy(self, x, y, state, use_lights=False):
        if self.flipped:
            y -= 1
        idx = self.get_note_index(x, y)
        octave = self.get_octave(x, y)
        try:
            self.board[y+self.flipped][x] = state
        except IndexError:
            print("mark_xy: Out of range")
            pass
        if use_lights:
            if state:
                self.set_light(x, y, 1)
            else:
                self.reset_light(x, y)
        self.dirty = True

    def mark(self, midinote, state, use_lights=False, only_row=None):
        if only_row is not None:
            only_row = self.board_h - only_row - 1 - self.flipped #flip
            rows = [self.board[only_row]]
            y = only_row
        else:
            rows = self.board
            y = 0
        for row in rows:
            x = 0
            for x in range(len(row)):
                idx = self.get_note_index(x, y)
                # print(x, y, midinote%12, idx)
                if midinote%12 == idx:
                    octave = self.get_octave(x, y)
                    if octave == midinote//12:
                        self.board[y+self.flipped][x] = state
                        if use_lights:
                            if state:
                                self.set_light(x, y, 1)
                            else:
                                self.reset_light(x, y)
            y += 1
        self.dirty = True

    def resize(self):
        self.board_sz = glm.ivec2(self.board_w, self.board_h)
        self.screen_w = self.board_w * self.scale.x
        self.screen_h = self.board_h * self.scale.y + self.menu_sz
        self.button_sz = self.screen_w / self.board_w
        self.screen_sz = glm.ivec2(self.screen_w, self.screen_h)
        self.screen = Screen(self,pygame.display.set_mode(self.screen_sz))
        self.dirty_lights = True

    def channel_from_split(self, row, col):
        if not self.options.split:
            return 0
        w = self.board_w
        col += 1 # move start point from C to A#
        col -= ((row+1)//2) # make the split line diagonal
        ch = 0 if col < w // 2 else 1 # channel 0 to 1 depending on split
        return ch

    def is_split(self):
        # TODO: make this work with hardware overlap (non-mpe)
        return self.options.no_overlap and self.options.split and self.split_out
    
    def logic(self, dt):

        keys = pygame.key.get_pressed()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.quit()
                break
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.quit()
                else:
                    try:
                        n = self.keys[ev.key]
                        n -= 12
                        self.mark(n + self.vis_octave * 12, 1, True)
                        data = [0x90, n, 127]
                        # TODO: add split for mouse?
                        if self.midi_out:
                            self.midi_write(self.midi_out, data, 0)
                    except KeyError:
                        pass
            elif ev.type == pygame.KEYUP:
                try:
                    n = self.keys[ev.key]
                    n -= 12
                    self.mark(n + self.vis_octave * 12, 0, True)
                    data = [0x80, n, 0]
                    if self.midi_out:
                        # TODO: add split for mouse?
                        self.midi_write(self.midi_out, data, 0)
                except KeyError:
                    pass
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                x, y = ev.pos
                y -= self.menu_sz
                if ev.button == 1:
                    self.mouse_press(x, y)
                elif ev.button == 2:
                    self.mouse_release(x, y)
                elif ev.button == 3:
                    self.mouse_hold(x, y)
            elif ev.type == pygame.MOUSEBUTTONUP:
                self.mouse_release()
            elif ev.type == pygame_gui.UI_BUTTON_PRESSED:
                if ev.ui_element == self.btn_octave_down:
                    self.octave -= 1
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_octave_up:
                    self.octave += 1
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_transpose_down:
                    self.transpose_board(-1)
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_transpose_up:
                    self.transpose_board(1)
                    self.dirty = self.dirty_lights = True
                # elif ev.ui_element == self.btn_mode:
                #     # TODO: toggle mode
                #     self.dirty = True
                elif ev.ui_element == self.btn_size:
                    if self.board_w == 16:
                        self.board_w = 25
                        self.resize()
                    else:
                        self.board_w = 16
                        self.resize()
                    self.dirty = True
                elif ev.ui_element == self.btn_rotate:
                    if self.rotated:
                        self.transpose += 3
                        self.rotated = False
                    else:
                        self.transpose -= 3
                        self.rotated = True
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_flip:
                    self.flipped = not self.flipped
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_split:
                    self.split_state = not self.split_state
                    self.btn_split.set_text("SPLIT: " + ("ON" if self.split_state else "OFF"))
                    self.dirty = True
            # elif ev.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            #     if ev.ui_element == self.slider_velocity:
            #         global self.options.velocity_curve
            #         self.options.velocity_curve = ev.value
            #         self.config_save_timer = 1.0
            
            self.gui.process_events(ev)

        # figure out the lowest note to highlight it
        if self.options.show_lowest_note:
            old_lowest_note = self.lowest_note
            old_lowest_note_midi = self.lowest_note_midi
            self.lowest_note = None
            self.lowest_note_midi = None
            note_count = 0
            for y, row in enumerate(self.board):
                for x, cell in enumerate(row):
                    if cell:
                        note_idx = self.get_note_index(x,y)
                        note_num = note_idx + 12*self.octaves[y][x]
                        if not self.lowest_note_midi or note_num < self.lowest_note_midi:
                            self.lowest_note = NOTES[note_idx]
                            self.lowest_note_midi = note_num
                        note_count+=1

        if self.dirty:
            self.init_board()
        
        if self.dirty_lights:
            self.setup_lights()
            self.dirty_lights = False

        # lowest note changed?
        if self.options.show_lowest_note:
            if self.lowest_note != old_lowest_note:
                if old_lowest_note:
                    # reset lights for previous lowest note
                    for y, row in enumerate(self.board):
                        for x, cell in enumerate(row):
                            if self.get_note(x,y) == old_lowest_note:
                                self.reset_light(x,y)
                if self.lowest_note:
                    # set lights for new lowest note
                    for y, row in enumerate(self.board):
                        for x, cell in enumerate(row):
                            if self.get_note(x,y) == self.lowest_note:
                                self.set_light(x,y,9)

        # if self.visualizer:
        #     while self.visualizer.poll():
        #         events = self.visualizer.read(100)
        #         for ev in events:
        #             data = ev[0]
        #             ch = data[0] & 0x0f
        #             msg = data[0] >> 4
        #             if msg == 9: # note on
        #                 self.mark(data[1] + self.vis_octave*12, 1, True)
        #             elif msg == 8: # note off
        #                 self.mark(data[1] + self.vis_octave*12, 0, True)

        # row_ofs = [
        #     0, -5, -10
        # ]
        # if self.midi_in:
        #     while self.midi_in.poll():
        #         events = self.midi_in.read(100)
        #         for ev in events:
        #             data = ev[0]
        #             d0 = data[0]
        #             ch = d0 & 0x0f
        #             msg = (data[0] & 0xf0) >> 4
        #             if self.options.one_channel:
        #                 data[0] = d0 & 0xf0 # send all to channel 0 if enabled
        #             row = None
        #             if not self.options.no_overlap:
        #                 row = ch % 8
        #                 col = ch // 8
        #             width = self.board_w//2 if self.options.hardware_split else self.board_w
        #             if msg == 9: # note on
        #                 # if WHOLETONE:
        #                 if self.options.no_overlap:
        #                     row = data[1] // width
        #                     col = data[1] % width
        #                     data[1] = data[1] % width + 30 + 2.5*row
        #                     data[1] *= 2
        #                     data[1] = int(data[1])
        #                     if self.options.hardware_split and ch >= 8:
        #                         data[1] += width * 2
        #                 else:
        #                     data[1] *= 2
        #                     try:
        #                         data[1] -= row * 5
        #                     except IndexError:
        #                         pass
                        
        #                 data[1] += (self.octave + self.octave_base) * 12
        #                 data[1] += BASE_OFFSET
        #                 midinote = data[1] - 24 + self.transpose*2
        #                 if self.is_split():
        #                     split_chan = self.channel_from_split(row, col)
        #                 self.mark(midinote, 1, only_row=row)
        #                 data[1] += self.out_octave * 12 + self.transpose*2
        #                 if self.flipped:
        #                     data[1] += 7
                        
        #                 # apply velocity curve
        #                 vel = data[2]/127
        #                 if self.has_velocity_settings():
        #                     vel = self.velocity_curve(data[2]/127)
        #                     data[2] = clamp(self.options.min_velocity,self.options.max_velocity,int(vel*127+0.5))

        #                 note = self.notes[ch]
        #                 if note.location is None:
        #                     note.location = glm.ivec2(0)
        #                 self.notes[ch].location.x = col
        #                 self.notes[ch].location.y = row
        #                 self.notes[ch].pressure = vel
                        
        #                 if self.is_split():
        #                     if split_chan == 0:
        #                         self.midi_out.write([[data, ev[1]]])
        #                     else:
        #                         self.split_out.write([[data, ev[1]]])
        #                 else:
        #                     self.midi_out.write([[data, ev[1]]])
                        
        #                 # print('note on: ', data)
        #             elif msg == 8: # note off
        #                 # if WHOLETONE:
        #                 if self.options.no_overlap:
        #                     row = data[1] // width
        #                     col = data[1] % width
        #                     data[1] = data[1] % width + 30 + 2.5*row
        #                     data[1] *= 2
        #                     data[1] = int(data[1])
        #                     if self.options.hardware_split and ch >= 8:
        #                         data[1] += width * 2
        #                 else:
        #                     data[1] *= 2
        #                     try:
        #                         data[1] -= row * 5
        #                     except IndexError:
        #                         pass
                        
        #                 data[1] += (self.octave + self.octave_base) * 12
        #                 data[1] += BASE_OFFSET
        #                 midinote = data[1] - 24 + self.transpose*2
        #                 if self.is_split():
        #                     split_chan = self.channel_from_split(row, col)
        #                 self.mark(midinote, 0, only_row=row)
        #                 data[1] += self.out_octave * 12 + self.transpose*2
        #                 if self.flipped:
        #                     data[1] += 7
                    
        #                 if self.is_split():
        #                     if split_chan == 0:
        #                         self.midi_out.write([[data, ev[1]]])
        #                     else:
        #                         self.split_out.write([[data, ev[1]]])
        #                 else:
        #                     self.midi_out.write([[data, ev[1]]])
        #                 # print('note off: ', data)
        #             # expression pedal
        #             # elif msg == 11: # sustain pedal
        #             #     if SUSTAIN is not None:
        #             #         sus = ev[0][2]
        #             #         ev[0][2] = int(round(clamp(0, 127, sus*SUSTAIN)))
        #             #         self.midi_out.write([[data, ev[1]]])
        #             #     else:
        #             #         self.midi_out.write([ev])
        #             elif 0xf0 <= msg <= 0xf7: # sysex
        #                 self.midi_out.write([ev])
        #             else:
        #                 # control change, aftertouch, pitch bend, etc...
        #                 if self.is_split():
        #                     note = self.notes[ch]
        #                     if note.location:
        #                         col = self.notes[ch].location.x
        #                         row = self.notes[ch].location.y
        #                         split_chan = self.channel_from_split(row, col)
        #                         if split_chan:
        #                             self.split_out.write([ev])
        #                         else:
        #                             self.midi_out.write([ev])
        #                     else:
        #                         self.midi_out.write([ev])
        #                 else:
        #                     self.midi_out.write([ev])
        #             # else: # sysex
        #             #     # if self.split_out:
        #             #     #     self.split_out.write([ev])
        #             #     # print(ch, msg)
        #             #     self.midi_out.write([ev])

        # # if self.config_save_timer > 0.0:
        # #     self.config_save_timer -= dt
        # #     if self.config_save_timer <= 0.0:
        # #         save()
        
        self.gui.update(dt)

    def sustainable_devices(self):
        if not self.is_split() or not self.options.sustain_split:
            return [self.midi_out]
        if self.options.sustain_split=='left':
            return [self.midi_out]
        elif self.options.sustain_split=='right':
            return [self.split_out]
        elif self.options.sustain_split=='both':
            return [self.midi_out, self.split_out]
        return [self.midi_out]

    def render(self):
        if not self.dirty:
            return
        self.dirty = False
        
        self.screen.surface.fill((0,0,0))
        b = 2 # border
        sz = self.screen_w / self.board_w
        y = 0
        rad = int(sz//2 - 8)
        
        for row in self.board:
            x = 0
            for cell in row:
                # write text
                note = self.get_note(x, y)

                split_chan = self.channel_from_split(y, x) # !
                
                # note = str(self.get_octave(x, y)) # show octave
                # brightness = 1.0 if cell else 0.5

                col = None
                
                # if cell:
                #     col = glm.ivec3(255,0,0)
                # else:
                #     col = self.get_color(x, y)
                lit_col = glm.ivec3(255,0,0)
                unlit_col = copy.copy(self.get_color(x, y))
                black = (unlit_col == glm.ivec3(0))
                inner_col = copy.copy(unlit_col)
                for i in range(len(unlit_col)):
                    unlit_col[i] = min(255, unlit_col[i] * 1.5)
                
                ry = y + self.menu_sz # real y
                # pygame.gfxdraw.box(self.screen.surface, [x*sz + b, self.menu_sz + y*sz + b, sz - b, sz - b], unlit_col)
                rect = [x*sz + b, self.menu_sz + y*sz + b, sz - b, sz - b]
                inner_rect = [rect[0]+4, rect[1]+4, rect[2]-8, rect[3]-8]
                pygame.draw.rect(self.screen.surface, unlit_col, rect, border_radius=8)
                pygame.draw.rect(self.screen.surface, inner_col, inner_rect, border_radius=8)
                if not black:
                    pygame.draw.rect(self.screen.surface, BORDER_COLOR, rect, width=2, border_radius=8)
                else:
                    pygame.draw.rect(self.screen.surface, glm.vec3(24), rect, width=2, border_radius=8)
                if cell:
                    circ = glm.ivec2(int(x*sz + b/2 + sz/2), int(self.menu_sz + y*sz + b/2 + sz/2))
                    pygame.gfxdraw.aacircle(self.screen.surface, circ.x+1, circ.y-1, rad, glm.ivec3(255,0,0))
                    pygame.gfxdraw.filled_circle(self.screen.surface, circ.x+1, circ.y-1, rad, glm.ivec3(255,0,0))

                    pygame.gfxdraw.aacircle(self.screen.surface, circ.x-1, circ.y+1, rad, glm.ivec3(0))
                    pygame.gfxdraw.filled_circle(self.screen.surface, circ.x-1, circ.y+1, rad, glm.ivec3(0))

                    pygame.gfxdraw.filled_circle(self.screen.surface, circ.x, circ.y, rad, lit_col)
                    pygame.gfxdraw.aacircle(self.screen.surface, circ.x, circ.y, rad, lit_col)

                    pygame.gfxdraw.filled_circle(self.screen.surface, circ.x, circ.y, int(rad*0.9), glm.ivec3(200,0,0))
                    pygame.gfxdraw.aacircle(self.screen.surface, circ.x, circ.y, int(rad*0.9), glm.ivec3(200,0,0))
                
                text = self.font.render(note, True, (0,0,0))
                textpos = text.get_rect()
                textpos.x = x*sz + sz//2 - FONT_SZ//4
                textpos.y = self.menu_sz + y*sz + sz//2 - FONT_SZ//4
                textpos.x -= 1
                textpos.y += 1
                self.screen.surface.blit(text, textpos)

                text = self.font.render(note, True, glm.ivec3(255))
                textpos = text.get_rect()
                textpos.x = x*sz + sz//2 - FONT_SZ//4
                textpos.y = self.menu_sz + y*sz + sz//2 - FONT_SZ//4
                textpos.x += 1
                textpos.y -= 1
                self.screen.surface.blit(text, textpos)
                
                text = self.font.render(note, True, glm.ivec3(200))
                textpos = text.get_rect()
                textpos.x = x*sz + sz//2 - FONT_SZ//4
                textpos.y = self.menu_sz + y*sz + sz//2 - FONT_SZ//4
                self.screen.surface.blit(text, textpos)

                x += 1
            y += 1

        # if CHORD_ANALYZER:
        #     self.render_chords()

    # def render_chords(self):
    #     sz = self.screen_w / self.board_w
    #     chords = set()
    #     for y, row in enumerate(self.board):
    #         ry = y + self.menu_sz # real y
    #         for x, cell in enumerate(row):
    #             # root_pos = glm.ivec2(0,0)
    #             for name, inversion_list in CHORD_SHAPES.items():
    #                 for shape in inversion_list:
    #                     next_chord = False
    #                     polygons = []
    #                     polygon = []
    #                     root = None
    #                     for rj, chord_row in enumerate(shape):
    #                         for ri, ch in enumerate(chord_row):
    #                             try:
    #                                 mark = self.board[y+rj][x+ri]
    #                             except:
    #                                 polygon = []
    #                                 next_chord = True
    #                                 break
    #                             # mark does not exist (not this chord)
    #                             if ch=='x':
    #                                 root = glm.ivec2(x+ri, y+rj)
    #                             if not mark and ch in 'ox':
    #                                 next_chord=True # double break
    #                                 polygon = []
    #                                 break
    #                             # polygon += [glm.ivec2((x+ri)*sz, (y+rj)*sz+self.menu_sz)]
    #                         if next_chord: # double break
    #                             break
    #                         # if polygon:
    #                         #     polygons += [polygon]
    #                     if not next_chord:
    #                         # for poly in polygons:
    #                         #     pygame.draw.polygon(self.screen.surface, glm.ivec3(0,255,0), poly, 2)
    #                         note = self.get_note_index(*root)
    #                         chords.add((note, name))

        # if chords:
        #     name = ', '.join(NOTES[c[0]] + c[1] for c in chords) # concat names
        #     text = self.font.render(name, True, glm.ivec3(255))
        #     textpos = text.get_rect()
        #     textpos.x = 0
        #     textpos.y = self.menu_sz // 2
        #     self.screen.surface.blit(text, textpos)

    def draw(self):
        self.gui.draw_ui(self.screen.surface)
        self.screen.render()
        pygame.display.flip()
        # self.root.update_idletasks()
        # self.root.update()

    def __call__(self):
        
        try:
            self.done = False
            while not self.done:
                try:
                    dt = self.clock.tick(self.options.fps)/1000.0
                except:
                    self.deinit()
                    break
                self.logic(dt)
                if self.done:
                    break
                self.render()
                self.draw()
        except:
            print(traceback.format_exc())
        
        self.deinit()
        
        return 0


    def deinit(self):
        for out in self.out:
            out.close()
            out.abort()
        self.out = []
        

def main():
    
    core = None
    try:
        core = Core()
        core()
    except:
        print(traceback.format_exc())
    del core
    pygame.midi.quit()
    pygame.display.quit()
    os._exit(0)
    # pygame.quit()

if __name__=='__main__':
    main()

