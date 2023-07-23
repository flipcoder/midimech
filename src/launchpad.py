from src.device import Device, DeviceSettings
import glm

class Launchpad(Device):
    def __init__(self, core, out, mode, index=0, octave_separation=0):
        super().__init__(core)
        self.out = out
        self.mode = mode
        self.index = index
        self.octave_separation = octave_separation

        # self.pos = glm.ivec2(0, 0)

    def button(self, x, y):
        if self.mode == 'lpx':
            if y == 0:
                if x == 0:
                    self.octave += 1
                    self.core.clear_marks(use_lights=False)
                elif x == 1:
                    self.octave -= 1
                    self.core.clear_marks(use_lights=False)
                elif x == 2:
                    self.core.move_board(-1)
                    # self.pos.x -= 1
                elif x == 3:
                    self.core.move_board(1)
                elif x == 4:
                    self.core.set_tonic(self.core.tonic - 1)
                elif x == 5:
                    self.core.set_tonic(self.core.tonic + 1)
            if x == 8:
                if y == 0:
                    self.core.next_scale()
                elif y == 1:
                    self.core.prev_scale()
                elif y == 2:
                    self.core.next_mode()
                elif y == 3:
                    self.core.prev_mode()

    def set_lights(self):
        if self.mode == "lpx":
            self.out.LedCtrlXY(0, 0, 0, 0, 63)
            self.out.LedCtrlXY(1, 0, 0, 0, 63)
            self.out.LedCtrlXY(2, 0, 63, 0, 63)
            self.out.LedCtrlXY(3, 0, 63, 0, 63)
            self.out.LedCtrlXY(4, 0, 63, 0, 0)
            self.out.LedCtrlXY(5, 0, 63, 0, 0)
            
            self.out.LedCtrlXY(8, 1, 63, 63, 0)
            self.out.LedCtrlXY(8, 2, 63, 63, 0)
            self.out.LedCtrlXY(8, 3, 0, 63, 63)
            self.out.LedCtrlXY(8, 4, 0, 63, 63)



    def get_octave(self):
        return self.octave_separation + self.octave

