#!/usr/bin/python3
import os,sys,glm,copy,binascii,struct,math,traceback
import pygame, pygame.midi, pygame.gfxdraw
import mido

OFFSET = 12
BOARD_W = 16
BOARD_H = 8
BOARD_SZ = glm.ivec2(BOARD_W, BOARD_H)
SCALE = glm.vec2(64.0)
SCREEN_W = BOARD_W * SCALE.x
SCREEN_H = BOARD_H * SCALE.y
SCREEN_SZ = glm.ivec2(SCREEN_W, SCREEN_H)
GFX = True
TITLE = "Linnstrument Visualizer"
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
    [3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6],
    [3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5],
    [2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5],
    [2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4],
    [1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4],
    [1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 4],
    [1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3],
    [0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3]
]

def get_octave(x, y):
    return OCTAVES[y - BOARD_H][x] + 1

def get_note_index(x, y):
    base_offset = -4
    ofs = (BOARD_H - y) // 2 + base_offset
    step = 2 if WHOLETONE else 1
    if y%2 == 1:
        return ((x-ofs)*step)%len(NOTES)
    else:
        return ((x-ofs)*step+7)%len(NOTES)

def get_note(x, y):
    return NOTES[get_note_index(x, y)]

def get_color(x, y):
    # return NOTE_COLORS[get_note_index(x, y)]
    note = get_note(x, y)
    if note in 'FB':
        return glm.ivec3(64)
    elif len(note) == 1:
        return glm.ivec3(127)
    else:
        return glm.ivec3(32)

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

class Core:
    def __init__(self):

        self.midi_fn = None
        self.midifile = None
        if len(sys.argv) > 1:
            self.midi_fn = sys.argv[1]
            if self.midi_fn.to_lower().endswith('.mid'):
                self.midifile = mido.MidiFile(midi_fn)

        if GFX:
            pygame.init()
            pygame.display.set_caption(TITLE)
            if FOCUS:
                pygame.mouse.set_visible(0)
                pygame.event.set_grab(True)
            self.screen = Screen(pygame.display.set_mode(SCREEN_SZ))
        
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

    def mark(self, midinote, state):
        y = 0
        # print('')
        # print("midi note: ", midinote)
        for row in self.board:
            x = 0
            for cell in row:
                idx = get_note_index(x, y)
                if midinote%12 == idx:
                    octave = get_octave(x, y)
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
                note = get_note(x, y)
                note = str(get_octave(x, y))

                col = None
                
                if cell:
                    col = glm.ivec3(255,0,0)
                else:
                    col = get_color(x, y)
                
                pygame.gfxdraw.box(self.screen.surface, [x*sz + b, y*sz + b, sz - b, sz - b], col)
                
                text = self.font.render(note, True, glm.ivec3(0))
                textpos = text.get_rect()
                textpos.x = x*sz + sz//2 - FONT_SZ//4
                textpos.y = y*sz + sz//2 - FONT_SZ//4
                text = self.font.render(note, True, glm.ivec3(255))
                self.screen.surface.blit(text, textpos)
                textpos = text.get_rect()
                textpos.x = x*sz + sz//2 - FONT_SZ//4
                textpos.y = y*sz + sz//2 - FONT_SZ//4
                textpos.x += 1
                textpos.y += 1
                self.screen.surface.blit(text, textpos)
                x += 1
            y += 1

    def draw(self):
        if not GFX:
            return
        
        self.screen.render()
        pygame.display.flip()

    def __call__(self):
        
        try:
            self.done = False
            while not self.done:
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

