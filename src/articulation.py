from enum import Enum
from src.util import sign
from src.constants import *

class Articulation:
    State = Enum('state', 'off pre attack hold release')
    
    def __init__(self, core):
        self.core = core
        self.value = 0.0
        self.time_between_ticks = 0.05
        self.timer = 0.0
        self.state = self.State(self.State.off)

        # a list of midi notes that need to be released
        self.deferred_notes = set()
        # self.noise_ = 0.0
        # self.last_noise = 0.0

        self.vibrato_low = 0.75
        self.vibrato_high = 0.85
        self.vibrato_dir = 0.0
        self.vibrato_window_t = 0.0
        self.vibrato_window = 0.5
        self.pressure_ = 0.0
        self.wiggles = 0
        
        self.mod = 0.0
        self.mod_changed = True

    def pressure(self, value):
        if not value or value <= 0.0:
            self.pressure_ = value
            self.wiggles = 0
            self.vibrato_dir = 1.0
            self.vibrato_window_t = 0.0
            return
        if self.pressure_ == 0.0: # was off, now on
            self.vibrato_dir = 1.0
            self.wiggles = 0
        self.pressure_ = value
        if value <= self.vibrato_low:
            if self.vibrato_dir <= 0.0:
                self.vibrato_dir = 1.0
        if value >= self.vibrato_high:
            if self.vibrato_dir >= 0.0:
                self.vibrato_window_t = self.vibrato_window
                self.vibrato_dir = -1.0
                self.wiggles += 1

    def change_state(self, new_state):
        if new_state == self.state:
            return
        if new_state == self.state.pre:
            self.state = new_state
            return
        if new_state == self.state.attack:
            self.state = new_state
            return
        if new_state == self.state.hold:
            self.state = new_state
            return
        if new_state == self.state.release:
            self.state = new_state
            return

    def release(self):
        self.change_state(self.state.release)

    def stop(self):
        self.change_state(self.state.off)

    def defer_midi_note(self, note):
        self.notes.add(note)

    def set(self, value):
        if self.value is False or self.value <= 0.0:
            if self.state != self.state.off:
                self.change_state(self.state.release)
        
        self.value = value or 0.0

        if self.state == self.state.off:
            self.change_state(self.state.pre)

    def tick(self):
        # if self.state == self.state.off:
        #     return

        if self.mod_changed:
            self.core.midi_write(self.core.midi_out, [0xb0, 1, int(self.mod * 127)])
            self.mod_changed = False
        
        # held_note_count = self.core.held_note_count()
        # if held_note_count == 0:
        #     pass

    def logic(self, dt):
        self.timer += dt
        
        self.vibrato_window_t = max(0.0, self.vibrato_window_t - 1.0 * dt)
        if self.vibrato_window_t <= 0.0:
            self.vibrato_length = 0.0
            self.wiggles = 0
            if self.mod >= 0.0:
                self.mod = 0.0
                self.mod_changed = True
        elif self.wiggles >= 2:
            if self.mod < 1.0:
                self.mod = min(1.0, self.mod + 1.0 * dt)
                self.mod_changed = True
        else:
            if self.mod > 0.0:
                self.mod = max(0.0, self.mod - 1.0 * dt)
                self.mod_changed = True
        
        if self.timer >= self.time_between_ticks:
            self.timer -= self.time_between_ticks
            
            # we're losing time
            if self.timer >= self.time_between_ticks:
                self.timer = 0.0

            self.tick()

