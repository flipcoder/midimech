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

PANEL = True
MENU_SZ = 64 if PANEL else 32
OFFSET = 12
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

CHORD_SHAPES = OrderedDict()
CHORD_SHAPES["maj7"] = [
    [
        " . o",
        "x o "
    ],
    [
        "x  ",
        ". o",
        " o "
    ],
    [
        "x o",
        ". o",
    ],
    [
        " . ",
        "x o",
        "  o"
    ]
]
CHORD_SHAPES["min7"] = [
    [
        " o ",
        "o .",
        " x "
    ],
    [
        " ox",
        "o .",
    ],
    [
        " o ",
        " ox",
        "  .",
    ],
    [
        "o .",
        "ox"
    ]

]
CHORD_SHAPES["sus2"] = [
    [
        " o",
        "xo "
    ]
]
CHORD_SHAPES["Q"] = [
    [
        "o",
        "o",
        "x"
    ]
]
CHORD_SHAPES["Qt"] = [
    [
        "  o",
        " o",
        "x"
    ]
]
CHORD_SHAPES["dim"] = [
    [
        "o",
        " o",
        "  x"
    ],
    [
        "o  x",
        " o",
    ],
    [
        "  x ",
        "o  o",
    ]
]
CHORD_SHAPES["aug"] = [
    [
        "x o o"
    ],
    [
        "x"
        "",
        " o o"
    ],
    [
        "x o"
        "",
        "   o"
    ]
]
CHORD_SHAPES["lyd"] = [
    [
        "x oo"
    ],
    [
        " x  ",
        "",
        "  oo"
    ],
    [
        "x o",
        "",
        "  o"
    ]

]
CHORD_SHAPES["sus4"] = [[
    "oo",
    "x "
]]
CHORD_SHAPES["dom7"] = [
    [
        "o ",
        " .",
        "x o"
    ],
    [
        "ox",
        " .",
        "  o"
    ],
    [
        "ox o",
        " .",
    ],
    [
        "  .",
        "ox o",
    ]

]
CHORD_SHAPES["maj"] = [
    [
        " o",
        "x o"
    ],
    [
        " x",
        " o",
        "  o"
    ],
    [
        "x o",
        "o"
    ]

]
CHORD_SHAPES["min"] = [
    [
        "o o",
        " x "
    ],
    [
        "  x",
        "o o",
    ],
    [
        " o",
        "  x",
        "  o",
    ]
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
    def get_octave(self, x, y):
        return OCTAVES[y - BOARD_H][x] + self.octave

    def get_note_index(self, x, y):
        x += self.transpose
        base_offset = -4
        ofs = (BOARD_H - y) // 2 + base_offset
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
        if note in 'FB':
            return glm.ivec3(64)
        elif len(note) == 1:
            return glm.ivec3(127)
        else:
            return glm.ivec3(32)
    
    def __init__(self):

        self.octave = 2
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
            'impact',
            'visualizer'
        ]
        out_devs = [
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

        innames = []
        outnames = []
        brk = False
        for outdev in out_devs:
            for out in outs:
                if outdev.lower() in out[1].lower():
                    outnames += [str(out[1])]
                    o = pygame.midi.Output(out[0])
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
            
        w = 16
        h = 8
        self.board = [[0 for x in range(w)] for y in range(h)]

        self.font = pygame.font.Font(None, FONT_SZ)
        self.retro_font = pygame.font.Font("PressStart2P.ttf", FONT_SZ)
        self.clock = pygame.time.Clock()

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
                    self.dirty = True
                elif ev.ui_element == self.btn_octave_up:
                    self.octave += 1
                    self.dirty = True
                elif ev.ui_element == self.btn_transpose_down:
                    self.transpose -= 1
                    self.dirty = True
                elif ev.ui_element == self.btn_transpose_up:
                    self.transpose += 1
                    self.dirty = True
                elif ev.ui_element == self.btn_mode:
                    # TODO: toggle mode
                    self.dirty = True

            self.gui.process_events(ev)
        
        if self.visualizer:
            while self.visualizer.poll():
                events = self.visualizer.read(100)
                for ev in events:
                    data = ev[0]
                    ch = data[0] & 0x0f
                    msg = data[0] >> 4
                    if msg == 9: # note on
                        self.mark(data[1], 1)
                    elif msg == 8: # note off
                        self.mark(data[1], 0)

        if self.midi:
            while self.midi.poll():
                events = self.midi.read(100)
                for ev in events:
                    data = ev[0]
                    ch = data[0] & 0x0f
                    msg = data[0] >> 4
                    if msg == 9: # note on
                        if WHOLETONE:
                            data[1] *= 2
                            data[1] -= OFFSET
                        self.out[0].write([ev])
                        # print('note on: ', data)
                    elif msg == 8: # note off
                        if WHOLETONE:
                            data[1] *= 2
                            data[1] -= OFFSET
                        self.out[0].write([ev])
                        # print('note off: ', data)
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

