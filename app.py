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
from chords import CHORD_SHAPES

PANEL = False
MENU_SZ = 64 if PANEL else 32
OFFSET = 0
BOARD_W = 16
BOARD_H = 8
BOARD_SZ = glm.ivec2(BOARD_W, BOARD_H)
SCALE = glm.vec2(64.0)
SCREEN_W = BOARD_W * SCALE.x
SCREEN_H = BOARD_H * SCALE.y + MENU_SZ
BUTTON_SZ = SCREEN_W / BOARD_W
SCREEN_SZ = glm.ivec2(SCREEN_W, SCREEN_H)
GFX = True
TITLE = "Whole-tone System for Linnstrument"
FOCUS = False
NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
WHOLETONE = True
FONT_SZ = 32
C_COLOR = glm.ivec3(0,32,0)
YELLOW = glm.ivec3(32,32,0)
LIGHT = glm.ivec3(0,0,32)
ALT = glm.ivec3(16)
GRAY = glm.ivec3(16)
DARK = glm.ivec3(0)
# LIGHT = glm.ivec3(127)
ONE_CHANNEL = False # send notes to first channel only (midi compat)
BASE_OFFSET = -4
CHORD_ANALYZER = False
EPSILON = 0.0001
# bend the velocity curve up or down range=[-1.0, 1.0], 0=default
VELOCITY_CURVE_BEND = 0.0

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

OCTAVES = [
    [3, 3, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6],
    [3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5],
    [2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5],
    [2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4],
    [1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4],
    [1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4],
    [1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],
    [0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3]
]

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
    def __init__(self,screen):
        self.pos = glm.vec2(0.0, 0.0)
        self.sz = glm.vec2(SCREEN_W, SCREEN_H)
        self.surface = pygame.Surface(SCREEN_SZ).convert()
        self.screen = screen
    
    def render(self):
        self.screen.blit(self.surface, (0,0))

def nothing():
    pass

class Core:

    def has_velocity_curve(self):
        return abs(VELOCITY_CURVE_BEND) > EPSILON

    def velocity_curve(self, val): # 0-1
        if self.has_velocity_curve():
            bend = val**2.0 if VELOCITY_CURVE_BEND < 0.0 else math.sqrt(val)
            newval = glm.mix(val, bend, abs(VELOCITY_CURVE_BEND))
            print(val, bend, newval)
            val = newval
        return val
    
    def send_cc(self, channel, cc, val):
        msg = mido.Message('control_change', channel=channel, control=cc, value=val)
        if not self.linn_out:
            return
        self.linn_out.write([[msg.bytes(),0]])

    def set_light(self, x, y, col): # col is [1,11], 0 resets
        self.send_cc(0, 20, x+1)
        self.send_cc(0, 21, BOARD_H - y - 1)
        self.send_cc(0, 22, col)

    def reset_light(self, x, y):
        note = self.get_note(x, y)
        pg_col = self.get_color(x, y)
        light_col = 0
        if pg_col is C_COLOR:
            light_col = 3
        elif pg_col is YELLOW:
            light_col = 2
        elif pg_col is GRAY:
            light_col = 5
        elif pg_col is DARK:
            light_col = 7
        elif pg_col is LIGHT:
            light_col = 5
        elif pg_col is ALT:
            light_col = 8
        self.set_light(x, y, light_col)
    
    def setup_lights(self):
        for y in range(BOARD_H):
            for x in range(BOARD_W):
                self.reset_light(x, y)
    
    def get_octave(self, x, y):
        return OCTAVES[y - BOARD_H][x] + self.octave

    def get_note_index(self, x, y):
        x += self.transpose
        ofs = (BOARD_H - y) // 2 + BASE_OFFSET
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
            if y%2==0:
                return ALT
            else:
                return LIGHT
        # # if note in 'FB':
        # #     return GRAY
        # elif len(note) == 1:
        #     if y%2==0:
        #         return LIGHT
        #     else:
        #         return ALT
        # else:
        return DARK
    
    def __init__(self):

        self.lowest_note = None # x,y location of lowest note currently pressed
        self.lowest_note_midi = None # midi number of lowest note currently pressed
        self.octave = 0
        self.out_octave = 0
        self.vis_octave = -2
        self.octave_base = -2
        self.transpose = 0
        
        self.midi_fn = None
        self.midifile = None
        if len(sys.argv) > 1:
            self.midi_fn = sys.argv[1]
            if self.midi_fn.to_lower().endswith('.mid'):
                self.midifile = mido.MidiFile(midi_fn)
        
        if GFX:
            # self.root = Tk()
            # self.menubar = Menu(self.root)
            # self.filemenu = Menu(self.menubar, tearoff=0)
            # self.filemenu.add_command(label="Open", command=nothing)
            # self.root.config(menu=self.menubar)
            # self.embed = Frame(self.root, width=SCREEN_W, height=SCREEN_H)
            # self.embed.pack()
            # os.environ['SDL_WINDOWID'] = str(self.embed.winfo_id())
            # self.root.update()
            # self.menubar.add_cascade(label="File", menu=self.filemenu)
            # self.root.protocol("WM_DELETE_WINDOW", self.quit)
            pygame.init()
            pygame.display.set_caption(TITLE)
            if FOCUS:
                pygame.mouse.set_visible(0)
                pygame.event.set_grab(True)
            self.screen = Screen(pygame.display.set_mode(SCREEN_SZ))
            
            bs = glm.ivec2(BUTTON_SZ,MENU_SZ//2 if PANEL else MENU_SZ) # button size
            self.gui = pygame_gui.UIManager(SCREEN_SZ)
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
            self.btn_mode = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((bs.x*4+2,y),bs),
                text='MODE',
                manager=self.gui
            )
        
        pygame.midi.init()
        
        self.out = []
        self.midi = None
        ins = []
        outs = []
        in_devs = [
            'linnstrument',
            'visualizer'
        ]
        out_devs = [
            'linnstrument',
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
        
        innames = []
        outnames = []
        brk = False
        for outdev in out_devs:
            for out in outs:
                if outdev.lower() in out[1].lower():
                    name = str(out[1])
                    outnames += [name]
                    o = pygame.midi.Output(out[0])
                    if 'linnstrument' in name.lower():
                        print("LinnStrument out: ", name)
                        self.linn_out = o
                    else:
                        self.out.append(o)

        if not self.out:
            oid = pygame.midi.get_default_output_id()
            o = pygame.midi.Output(oid)
            self.out.append(o)

        self.midi = None
        self.visualizer = None

        # print('outs: ' + ', '.join(outnames))
        # print('ins: ' + ', '.join(innames))
        
        for indev in in_devs:
            i = 0
            for ini in ins:
                if indev.lower() in ini[1].lower():
                    name = str(ini[1])
                    innames += [name]
                    if "visualizer" in name:
                        print("Visualizer MIDI: " + name)
                        inp = pygame.midi.Input(ini[0])
                        self.visualizer = inp
                    elif not 'MIDIIN' in name:
                        print("Instrument MIDI: " + name)
                        try:
                            inp = pygame.midi.Input(ini[0])
                            self.midi = inp
                        except:
                            print("Warning: MIDI DEVICE IN USE")
                i += 1
        
        # self.midi = None
        # if ins:
        #     # try:
        #     print("Using Midi input: ", ins[1])
        #     self.midi = pygame.midi.Input(ins[1][0])
        #     # except:
        #     #     pass
        
        self.done = False
        
        self.dirty = True
        self.dirty_lights = True
            
        w = 16
        h = 8
        self.board = [[0 for x in range(w)] for y in range(h)]

        self.font = pygame.font.Font(None, FONT_SZ)
        # self.retro_font = pygame.font.Font("PressStart2P.ttf", FONT_SZ)
        self.clock = pygame.time.Clock()

        self.setup_lights()

    def quit(self):
        self.done = True

    def mark(self, midinote, state):
        y = 0
        # print('')
        # print("midi note: ", midinote)
        for row in self.board:
            x = 0
            for cell in row:
                idx = self.get_note_index(x, y)
                if midinote%12 == idx:
                    octave = self.get_octave(x, y)
                    if octave == midinote//12:
                        # print(x,y)
                        self.board[y][x] = state
                x += 1
            y += 1
        self.dirty = True

    def logic(self, t):
        keys = pygame.key.get_pressed()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.done = True
                break
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.done = True
            elif ev.type == pygame_gui.UI_BUTTON_PRESSED:
                if ev.ui_element == self.btn_octave_down:
                    self.octave -= 1
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_octave_up:
                    self.octave += 1
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_transpose_down:
                    self.transpose -= 1
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_transpose_up:
                    self.transpose += 1
                    self.dirty = self.dirty_lights = True
                elif ev.ui_element == self.btn_mode:
                    # TODO: toggle mode
                    self.dirty = self.dirty_lights = True

            self.gui.process_events(ev)

        # figure out the lowest note to highlight it
        old_lowest_note = self.lowest_note
        old_lowest_note_midi = self.lowest_note_midi
        self.lowest_note = None
        self.lowest_note_midi = None
        note_count = 0
        for y, row in enumerate(self.board):
            for x, cell in enumerate(row):
                if cell:
                    note_idx = self.get_note_index(x,y)
                    note_num = note_idx + 12*OCTAVES[y][x]
                    if not self.lowest_note_midi or note_num < self.lowest_note_midi:
                        self.lowest_note = NOTES[note_idx]
                        self.lowest_note_midi = note_num
                    note_count+=1

        if self.dirty_lights:
            self.setup_lights()
            self.dirty_lights = False

        # lowest note changed?
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
                            self.set_light(x,y,1)

        if self.visualizer:
            while self.visualizer.poll():
                events = self.visualizer.read(100)
                for ev in events:
                    data = ev[0]
                    ch = data[0] & 0x0f
                    msg = data[0] >> 4
                    if msg == 9: # note on
                        self.mark(data[1] + self.vis_octave*12, 1)
                    elif msg == 8: # note off
                        self.mark(data[1] + self.vis_octave*12, 0)

        # row_ofs = [
        #     0, -5, -10
        # ]
        if self.midi:
            while self.midi.poll():
                events = self.midi.read(100)
                for ev in events:
                    data = ev[0]
                    d0 = data[0]
                    ch = d0 & 0x0f
                    if ONE_CHANNEL:
                        data[0] = d0 & 0xf0 # TEMP: send all to channel 0
                    msg = data[0] >> 4
                    row = ch % 8
                    if msg == 9: # note on
                        if WHOLETONE:
                            data[1] *= 2
                            try:
                                data[1] -= row * 5
                            except IndexError:
                                pass
                            data[1] += (self.octave + self.octave_base) * 12
                        data[1] += BASE_OFFSET
                        self.mark(data[1] - 24, 1)
                        data[1] += self.out_octave * 12
                        self.out[0].write([[data, ev[1]]])
                        # print('note on: ', data)
                    elif msg == 8: # note off
                        if WHOLETONE:
                            data[1] *= 2
                            try:
                                data[1] -= row * 5
                            except IndexError:
                                pass
                            data[1] += (self.octave + self.octave_base) * 12
                        data[1] += BASE_OFFSET
                        self.mark(data[1] - 24, 0)
                        data[1] += self.out_octave * 12
                        # self.out[0].write([ev])
                        self.out[0].write([[data, ev[1]]])
                        # print('note off: ', data)
                    elif msg == 14: # pitch bend
                        # val = (data[2]-64)/64 + data[1]/127/64
                        # val *= 2
                        self.out[0].write([ev])
                    else:
                        self.out[0].write([ev])
        
        self.gui.update(t)

    def render(self):
        if not GFX:
            return
        if not self.dirty:
            return
        self.dirty = False
        
        self.screen.surface.fill((0,0,0))
        b = 2 # border
        sz = SCREEN_W / BOARD_W
        y = 0
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
                
                ry = y + MENU_SZ # real y
                pygame.gfxdraw.box(self.screen.surface, [x*sz + b, MENU_SZ + y*sz + b, sz - b, sz - b], unlit_col)
                if cell:
                    pygame.gfxdraw.filled_circle(self.screen.surface, int(x*sz + b/2 + sz/2), int(MENU_SZ + y*sz + b/2 + sz/2), int(sz//2 - 8), lit_col)
                    pygame.gfxdraw.aacircle(self.screen.surface, int(x*sz + b/2 + sz/2), int(MENU_SZ + y*sz + b/2 + sz/2), int(sz//2 - 8), lit_col)
                
                text = self.font.render(note, True, glm.ivec3(0))
                textpos = text.get_rect()
                textpos.x = x*sz + sz//2 - FONT_SZ//4
                textpos.y = ry*sz + sz//2 - FONT_SZ//4
                self.screen.surface.blit(text, textpos)
                text = self.font.render(note, True, glm.ivec3(255))
                textpos = text.get_rect()
                textpos.x = x*sz + sz//2 - FONT_SZ//4
                textpos.y = MENU_SZ + y*sz + sz//2 - FONT_SZ//4
                textpos.x += 1
                textpos.y += 1
                self.screen.surface.blit(text, textpos)
                x += 1
            y += 1

        if CHORD_ANALYZER:
            self.render_chords()

    def render_chords(self):
        sz = SCREEN_W / BOARD_W
        chords = set()
        for y, row in enumerate(self.board):
            ry = y + MENU_SZ # real y
            for x, cell in enumerate(row):
                # root_pos = glm.ivec2(0,0)
                for name, inversion_list in CHORD_SHAPES.items():
                    for shape in inversion_list:
                        next_chord = False
                        polygons = []
                        polygon = []
                        root = None
                        for rj, chord_row in enumerate(shape):
                            for ri, ch in enumerate(chord_row):
                                try:
                                    mark = self.board[y+rj][x+ri]
                                except:
                                    polygon = []
                                    next_chord = True
                                    break
                                # mark does not exist (not this chord)
                                if ch=='x':
                                    root = glm.ivec2(x+ri, y+rj)
                                if not mark and ch in 'ox':
                                    next_chord=True # double break
                                    polygon = []
                                    break
                                # polygon += [glm.ivec2((x+ri)*sz, (y+rj)*sz+MENU_SZ)]
                            if next_chord: # double break
                                break
                            # if polygon:
                            #     polygons += [polygon]
                        if not next_chord:
                            # for poly in polygons:
                            #     pygame.draw.polygon(self.screen.surface, glm.ivec3(0,255,0), poly, 2)
                            note = self.get_note_index(*root)
                            chords.add((note, name))

        if chords:
            name = ', '.join(NOTES[c[0]] + c[1] for c in chords) # concat names
            text = self.font.render(name, True, glm.ivec3(255))
            textpos = text.get_rect()
            textpos.x = 0
            textpos.y = MENU_SZ // 2
            self.screen.surface.blit(text, textpos)

    def draw(self):
        if not GFX:
            return
        
        self.screen.render()
        self.gui.draw_ui(self.screen.surface)
        pygame.display.flip()
        # self.root.update_idletasks()
        # self.root.update()

    def __call__(self):
        
        try:
            self.done = False
            while not self.done:
                # t = self.clock.tick(60)/1000.0
                t = 0.0
                self.logic(t)
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

