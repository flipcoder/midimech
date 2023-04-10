#!/usr/bin/python3
# from tkinter import *
import os,sys,glm,copy,binascii,struct,math,traceback
with open(os.devnull, 'w') as devnull:
    # suppress pygame messages
    stdout = sys.stdout
    sys.stdout = devnull
    import pygame, pygame.midi, pygame.gfxdraw
    sys.stdout = stdout
import pygame_gui
import mido
from collections import OrderedDict
# from chords import CHORD_SHAPES
from configparser import ConfigParser

def get_option(section, option, default):
    if section is None: return default
    typ = type(default)
    if typ is bool:
        return section.get(option, 'true' if default else 'false').lower() in ['true','yes','on']
    if typ is int:
        return int(section.get(option, default))
    if typ is float:
        return float(section.get(option, default))
    if typ is str:
        return section.get(option, default)
    print('Invalid option value for', option)

cfg = ConfigParser(allow_no_value=True)
cfg.read('settings.ini')
try:
    opts = cfg['general']
except KeyError:
    opts = None

default_lights = '3,7,5,7,5,8,7,8,2,8,7,8'
OFFSET = 0
TITLE = "Linnstrument-Wholetone"
# FOCUS = False
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
WHOLETONE = True
FONT_SZ = 32
C_COLOR = glm.ivec3(0,128,0)
YELLOW = glm.ivec3(205,127,0)
LIGHT = glm.ivec3(0,0,128)
FGAB = glm.ivec3(64)
GRAY = glm.ivec3(16)
BORDER_COLOR = glm.ivec3(32)
DARK = glm.ivec3(0)
# LIGHT = glm.ivec3(127)
LIGHTS = get_option(opts,'lights',default_lights)
if LIGHTS:
    LIGHTS = list(map(lambda x: int(x), LIGHTS.split(',')))
ONE_CHANNEL = get_option(opts,'one_channel',False)
BASE_OFFSET = -4
# CHORD_ANALYZER = get_option(opts,'chord_analyzer',False)
EPSILON = 0.0001
# bend the velocity curve, examples: 0.5=sqrt, 1.0=default, 2.0=squared
VELOCITY_CURVE = get_option(opts,'velocity_curve',1.0)
if VELOCITY_CURVE < EPSILON: # if its near zero, set default
    VELOCITY_CURVE = 1.0 # default
MIN_VELOCITY = get_option(opts,'min_velocity',0)
MAX_VELOCITY = get_option(opts,'max_velocity',127)
CORE = None
SHOW_LOWEST_NOTE = get_option(opts,'show_lowest_note',True)
NO_OVERLAP = get_option(opts,'no_overlap',False)
HARDWARE_SPLIT = get_option(opts,'hardware_split',False)
MIDI_OUT = get_option(opts,'midi_out','loopmidi')
SPLIT_OUT = get_option(opts,'split_out','split')
FPS = get_option(opts,'fps',60)
SPLIT = get_option(opts,'split',False)
SUSTAIN = get_option(opts,'sustain',1.0) # sustain scale

def save():
    cfg = ConfigParser(allow_no_value=True)
    general = cfg['general'] = {}
    if LIGHTS:
        general['lights'] = ','.join(map(str,LIGHTS))
    general['one_channel'] = ONE_CHANNEL
    general['velocity_curve'] = VELOCITY_CURVE
    general['min_velocity'] = MIN_VELOCITY
    general['max_velocity'] = MAX_VELOCITY
    general['no_overlap'] = NO_OVERLAP
    general['hardware_split'] = HARDWARE_SPLIT
    general['show_lowest_note'] = SHOW_LOWEST_NOTE
    general['midi_out'] = MIDI_OUT
    general['split_out'] = SPLIT_OUT
    general['split'] = SPLIT
    general['fps'] = FPS
    general['sustain'] = SUSTAIN
    cfg['general'] = general
    with open('settings_temp.ini', 'w') as configfile:
        cfg.write(configfile)
    
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

class Object:
   def __init__(self, **kwargs):
        self.game = kwargs.get('game', None)
        self.attached = False
        if self.game:
            self.game.world.attach(self)
        
        self.pos = glm.vec2(*kwargs.get('pos', (0.0, 0.0)))
        self.vel = glm.vec2(*kwargs.get('vel', (0.0, 0.0)))
        self.sz = glm.vec2(*kwargs.get('sz', (0.0, 0.0)))
        self.surface = kwargs.get('surface', None)

class Screen(Object):
    def __init__(self,core,screen):
        self.core = core
        self.pos = glm.vec2(0.0, 0.0)
        self.sz = glm.vec2(core.screen_w, core.screen_h)
        self.surface = pygame.Surface(core.screen_sz).convert()
        self.screen = screen
    
    def render(self):
        self.screen.blit(self.surface, (0,0))

def nothing():
    pass

class Core:

    def has_velocity_curve(self):
        return abs(VELOCITY_CURVE - 1.0) > EPSILON

    def has_velocity_settings(self):
        return MIN_VELOCITY > 0 or MAX_VELOCITY < 127 or self.has_velocity_curve()

    def velocity_curve(self, val): # 0-1
        if self.has_velocity_curve():
            val = val**VELOCITY_CURVE
        return val
    
    def send_cc(self, channel, cc, val):
        msg = mido.Message('control_change', channel=channel, control=cc, value=val)
        # print(msg)
        if not self.linn_out:
            return
        self.linn_out.write([[msg.bytes(),0]])

    def set_light(self, x, y, col): # col is [1,11], 0 resets
        self.red_lights[y][x] = (col==1)
        self.send_cc(0, 20, x+1)
        self.send_cc(0, 21, self.board_h - y - 1)
        # if LIGHTS:
        self.send_cc(0, 22, col)
        # else:
        #     self.send_cc(0, 22, 7) # no light

    def reset_light(self, x, y):
        if not LIGHTS: return
        note = self.get_note_index(x, y) % 12
        light_col = LIGHTS[note]
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
        note = self.get_note(x, y)
        if note == "C":
            return C_COLOR
        # if note == "G#":
        #     return GSHARP_COLOR
        elif note == "G#":
            return YELLOW
        elif len(note) == 1: # white key
            if y%2==self.flipped:
                return FGAB
            else:
                return LIGHT
        # # if note in 'FB':
        # #     return GRAY
        # elif len(note) == 1:
        #     if y%2==0:
        #         return LIGHT
        #     else:
        #         return FGAB
        # else:
        return DARK

    # Given an x,y position, find the octave
    #  (used to initialize octaves 2D array)
    def init_octave(self, x, y):
        return int((x+4+self.transpose+y*2.5)//6)
    
    def init_octaves(self):
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
        for y in range(self.board_h+1): # make an extra mode for flipping
            self.octaves.append([])
            for x in range(self.max_width):
                self.octaves[y].append(self.init_octave(x, y))
        self.octaves = list(reversed(self.octaves))
    
    def __init__(self):

        global CORE
        CORE = self

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
        self.vis_octave = -3
        self.octave_base = -2
        self.transpose = 0
        self.rotated = False # transpose -3 whole steps
        self.flipped = False # vertically shift +1
        self.config_save_timer = 1.0

        self.init_octaves()
        
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
        # self.slider_label = pygame_gui.elements.UILabel(
        #     relative_rect=pygame.Rect((0,y+bs.y),(bs.x*2,bs.y)),
        #     text='Velocity Curve',
        #     manager=self.gui
        # )
        # self.slider_velocity = pygame_gui.elements.UIHorizontalSlider (
        #     relative_rect=pygame.Rect((bs.x*2+2,y+bs.y),(bs.x*2,bs.y)),
        #     start_value=VELOCITY_CURVE,
        #     value_range=[0,1],
        #     manager=self.gui
        # )
        
        pygame.midi.init()
        
        self.out = []
        self.midi_in = None
        ins = []
        outs = []
        in_devs = [
            'linnstrument',
            'visualizer'
        ]
        out_devs = [
            'linnstrument',
            MIDI_OUT,
            'loopmidi'
        ]
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            # print(info)
            if info[2]==1:
                ins.append((i,str(info[1])))
            if info[3]==1:
                outs.append((i,str(info[1])))

        # innames = []
        # for inx in ins:
        #     innames += [str(inx[1])]
        #     print('in: ', inx)

        self.linn_out = None
        self.midi_out = None
        self.split_out = None
        
        # innames = []
        # outnames = []
        brk = False
        # for outdev in out_devs:
        for out in outs:
            name = str(out[1])
            name_lower = name.lower()
            if 'linnstrument' in name_lower:
                print("Instrument Output: ", name)
                self.linn_out = pygame.midi.Output(out[0])
            elif not SPLIT_OUT is None and SPLIT_OUT in name_lower:
                print("MIDI Output (Split): ", name)
                self.split_out = pygame.midi.Output(out[0])
            elif MIDI_OUT in name_lower:
                print("MIDI Output: ", name)
                self.midi_out = pygame.midi.Output(out[0])

        if not self.linn_out:
            print("No LinnStrument output device detected. (Can't control lights)")
        if not self.midi_out:
            print("No MIDI output device detected. (Did you install LoopMidi?)")

        # if not self.out:
        #     oid = pygame.midi.get_default_output_id()
        #     o = pygame.midi.Output(oid)
        #     self.out.append(o)

        self.midi_in = None
        self.visualizer = None

        # print('outs: ' + ', '.join(outnames))
        # print('ins: ' + ', '.join(innames))
        
        # for indev in in_devs:
            # i = 0
        for ini in ins:
            # if indev.lower() in ini[1].lower():
            name = str(ini[1])
            # innames += [name]
            if "visualizer" in name:
                print("Visualizer Input: " + name)
                inp = pygame.midi.Input(ini[0])
                self.visualizer = inp
            elif 'linnstrument' in name.lower():
                print("Instrument Input: " + name)
                try:
                    self.midi_in = pygame.midi.Input(ini[0])
                except:
                    print("Warning: MIDI DEVICE IN USE")
            i += 1
        
        # self.midi_in = None
        # if ins:
        #     # try:
        #     print("Using Midi input: ", ins[1])
        #     self.midi_in = pygame.midi.Input(ins[1][0])
        #     # except:
        #     #     pass
        
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

    def mark(self, midinote, state, use_lights=False, only_row=None):
        if only_row is not None:
            only_row = self.board_h - only_row - 1 #flip
            rows = [self.board[only_row]]
            y = only_row
        else:
            rows = self.board
            y = 0
        for row in rows:
            x = 0
            for x in range(len(row)):
                idx = self.get_note_index(x, y)
                if midinote%12 == idx:
                    octave = self.get_octave(x, y)
                    if octave == midinote//12:
                        self.board[y][x] = state
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
        if not SPLIT:
            return 0
        w = self.board_w
        col += 1 # move start point from C to A#
        col -= ((row+1)//2) # make the split line diagonal
        ch = 0 if col < w // 2 else 1 # channel 0 to 1 depending on split
        return ch
    
    def logic(self, dt):

        keys = pygame.key.get_pressed()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.quit()
                break
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.quit()
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
            # elif ev.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            #     if ev.ui_element == self.slider_velocity:
            #         global VELOCITY_CURVE
            #         VELOCITY_CURVE = ev.value
            #         self.config_save_timer = 1.0
                
            self.gui.process_events(ev)

        # figure out the lowest note to highlight it
        if SHOW_LOWEST_NOTE:
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
            self.init_octaves()
        
        if self.dirty_lights:
            self.setup_lights()
            self.dirty_lights = False

        # lowest note changed?
        if SHOW_LOWEST_NOTE:
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

        if self.visualizer:
            while self.visualizer.poll():
                events = self.visualizer.read(100)
                for ev in events:
                    data = ev[0]
                    ch = data[0] & 0x0f
                    msg = data[0] >> 4
                    if msg == 9: # note on
                        self.mark(data[1] + self.vis_octave*12, 1, True)
                    elif msg == 8: # note off
                        self.mark(data[1] + self.vis_octave*12, 0, True)

        # row_ofs = [
        #     0, -5, -10
        # ]
        if self.midi_in:
            while self.midi_in.poll():
                events = self.midi_in.read(100)
                for ev in events:
                    data = ev[0]
                    d0 = data[0]
                    ch = d0 & 0x0f
                    if ONE_CHANNEL:
                        data[0] = d0 & 0xf0 # send all to channel 0 if enabled
                    msg = data[0] >> 4
                    row = None
                    if not NO_OVERLAP:
                        row = ch % 8
                    width = self.board_w//2 if HARDWARE_SPLIT else self.board_w
                    if msg == 9: # note on
                        # if WHOLETONE:
                        if NO_OVERLAP:
                            row = data[1] // width
                            col = data[1] % width
                            data[1] = data[1] % width + 30 + 2.5*row
                            data[1] *= 2
                            data[1] = int(data[1])
                            if HARDWARE_SPLIT and ch >= 8:
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
                        if SPLIT_OUT and self.split_out:
                            split_chan = self.channel_from_split(row, col)
                        self.mark(midinote, 1, only_row=row)
                        data[1] += self.out_octave * 12 + self.transpose*2
                        if self.flipped:
                            data[1] += 7
                        
                        # apply velocity curve
                        if self.has_velocity_settings():
                            vel = self.velocity_curve(data[2]/127)
                            data[2] = clamp(MIN_VELOCITY,MAX_VELOCITY,int(vel*127+0.5))
                            
                        if SPLIT_OUT and self.split_out:
                            if split_chan == 0:
                                self.midi_out.write([[data, ev[1]]])
                            else:
                                self.split_out.write([[data, ev[1]]])
                        else:
                            self.midi_out.write([[data, ev[1]]])
                        
                        # print('note on: ', data)
                    elif msg == 8: # note off
                        # if WHOLETONE:
                        if NO_OVERLAP:
                            row = data[1] // width
                            col = data[1] % width
                            data[1] = data[1] % width + 30 + 2.5*row
                            data[1] *= 2
                            data[1] = int(data[1])
                            if HARDWARE_SPLIT and ch >= 8:
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
                        if SPLIT_OUT and self.split_out:
                            split_chan = self.channel_from_split(row, col)
                        self.mark(midinote, 0, only_row=row)
                        data[1] += self.out_octave * 12 + self.transpose*2
                        if self.flipped:
                            data[1] += 7
                    
                        if SPLIT_OUT and self.split_out:
                            if split_chan == 0:
                                self.midi_out.write([[data, ev[1]]])
                            else:
                                self.split_out.write([[data, ev[1]]])
                        else:
                            self.midi_out.write([[data, ev[1]]])
                        # print('note off: ', data)
                    elif msg == 11: # sustain pedal
                        if SUSTAIN is not None:
                            sus = ev[0][2]
                            ev[0][2] = int(round(clamp(0, 127, sus*SUSTAIN)))
                            self.midi_out.write([[data, ev[1]]])
                        else:
                            self.midi_out.write([ev])
                    elif msg == 14: # pitch bend
                        # val = (data[2]-64)/64 + data[1]/127/64
                        # val *= 2
                        if SPLIT_OUT and self.split_out:
                            self.split_out.write([ev])
                        self.midi_out.write([ev])
                    else:
                        # if self.split_out:
                        #     self.split_out.write([ev])
                        # print(ch, msg)
                        self.midi_out.write([ev])

        # if self.config_save_timer > 0.0:
        #     self.config_save_timer -= dt
        #     if self.config_save_timer <= 0.0:
        #         save()
        
        self.gui.update(dt)

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
                # note = str(self.get_octave(x, y)) # show octave

                col = None
                
                # if cell:
                #     col = glm.ivec3(255,0,0)
                # else:
                #     col = self.get_color(x, y)
                lit_col = glm.ivec3(255,0,0)
                unlit_col = self.get_color(x, y)
                
                ry = y + self.menu_sz # real y
                # pygame.gfxdraw.box(self.screen.surface, [x*sz + b, self.menu_sz + y*sz + b, sz - b, sz - b], unlit_col)
                rect = [x*sz + b, self.menu_sz + y*sz + b, sz - b, sz - b]
                pygame.draw.rect(self.screen.surface, unlit_col, rect, border_radius=8)
                pygame.draw.rect(self.screen.surface, BORDER_COLOR, rect, width=2, border_radius=8)
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
        self.screen.render()
        self.gui.draw_ui(self.screen.surface)
        pygame.display.flip()
        # self.root.update_idletasks()
        # self.root.update()

    def __call__(self):
        
        try:
            self.done = False
            while not self.done:
                dt = self.clock.tick(FPS)/1000.0
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

