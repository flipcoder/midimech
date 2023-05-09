import pygame
from glm import ivec2, vec2, length
from src.util import sign

class Gamepad:
    def __init__(self, core, num=0):
        self.core = core
        self.joy = pygame.joystick.Joystick(num)
        self.notes = [None] * 16
        for i, note in enumerate(self.notes):
            self.notes[i] = set()
        self.cursors = [ivec2(4, 5), ivec2(5, 2)]
        self.offset = [vec2(0, 0), vec2(0,0)]
        self.ioffset = [ivec2(0, 0), ivec2(0, 0)]
        self.deadzone = 0.1
    def positions(self):
        return [self.cursors[0] + self.ioffset[0], self.cursors[1] + self.ioffset[1]]
    def logic(self, dt):
        for ofs_idx in range(2):
            for axis, value in enumerate(self.offset[ofs_idx]):
                self.ioffset[ofs_idx][axis%2] = int(round(value))
                # fix corners
                if abs(self.offset[ofs_idx].x) > 0.6 and abs(self.offset[ofs_idx].y) > 0.6:
                    self.ioffset[ofs_idx] = ivec2(sign(self.offset[ofs_idx].x), sign(self.offset[ofs_idx].y))
            # print(self.ioffset)
        self.core.dirty = True
    def play(self, ch, x, y, vel):
        note = y * 8 + x
        self.core.note_on([144, note, 100], 0, width=8, mpe=True)
        self.notes[ch].add(note)
    def event(self, ev):
        if ev.type == pygame.JOYAXISMOTION:
            axis = ev.axis
            # print(axis)
            if 2 <= axis < 4:
                self.offset[1][axis-2] = ev.value
            elif 0 <= axis < 2:
                self.offset[0][axis] = ev.value
        elif ev.type  == pygame.JOYHATMOTION:
            self.cursors[0] += ivec2(ev.value[0], -ev.value[1])
        elif ev.type  == pygame.JOYBUTTONUP:
            for note in self.notes[ev.button]:
                self.core.note_off([128, note, 100], 0, width=8, mpe=True)
        elif ev.type  == pygame.JOYBUTTONDOWN:
            for note in self.notes[ev.button]:
                self.core.note_off([128, note, 100], 0, width=8, mpe=True)
            if ev.button in (0, 1):
                pos = self.positions()[ev.button]
            elif ev.button == 2:
                pos = self.positions()[0] + ivec2(2,0)
            elif ev.button == 3:
                pos = self.positions()[1] + ivec2(2,0)
            x = pos.x
            y = self.core.board_h - pos.y - 1
            self.play(ev.button, x, y, 100)

