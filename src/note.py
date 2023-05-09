class Note:
    def __init__(self):
        # self.bend = 0.0
        # self.pressed = False
        # self.intensity = 0.0  # how much to light marker up (in app)
        self.ipressure = 0 # 0, 127
        self.pressure = 0.0  # how much the note is being pressed
        # self.dirty = False
        self.location = None  # on board
        self.midinote = None
        self.split = 0
        self.note = None

    # def logic(self, dt):
    #     if self.pressed:  # pressed, fade to pressure value
    #         if self.intensity != self.pressure:
    #             self.dirty = True
    #             if self.intensity < self.pressure:
    #                 self.intensity = min(pressure, self.intensity + dt * FADE_SPEED)
    #             else:
    #                 self.intensity = max(pressure, self.intensity - dt * FADE_SPEED)
    #     else:  # not pressed, fade out
    #         if self.intensity > 0.0:
    #             self.dirty = True
    #             self.pressure = 0.0
    #             self.intensity = max(0.0, self.intensity - dt * FADE_SPEED)




