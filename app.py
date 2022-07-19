#!/usr/bin/python3
import os
import sys
import pygame
import pygame.midi
import traceback

OFFSET = 12

GFX = False

class Core:
    def __init__(self):
        pygame.midi.init()
        
        self.out = []
        self.midi = None
        ins = []
        outs = []
        out_devs = [
            'loopmidi'
        ]
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            if info[2]==1:
                # input
                ins.append((i,str(info[1])))
            if info[3]==1:
                outs.append((i,str(info[1])))

        innames = []
        for inx in ins:
            innames += [str(inx[1])]
            print('in: ', inx)

        outnames = []
        brk = False
        for outdev in out_devs:
            for out in outs:
                if outdev.lower() in out[1].lower():
                    outnames += [out[1]]
                    o = pygame.midi.Output(out[0])
                    self.out.append(o)

        if not self.out:
            oid = pygame.midi.get_default_output_id()
            o = pygame.midi.Output(oid)
            self.out.append(o)

        print('outs: ' + ', '.join(outnames))
        print('ins: ' + ', '.join(innames))
        
        if ins:
            self.midi = pygame.midi.Input(ins[1][0])
        
        self.done = False

    def logic(self, t):
        if self.midi.poll():
            events = self.midi.read(10)
            for ev in events:
                data = ev[0]
                ch = data[0] & 0x0f
                msg = data[0] >> 4
                if msg == 9: # note on
                    data[1] *= 2
                    data[1] -= OFFSET
                    self.out[0].write([ev])
                    print('note on: ', data)
                elif msg == 8: # note off
                    data[1] *= 2
                    data[1] -= OFFSET
                    self.out[0].write([ev])
                    print('note off: ', data)
                else:
                    self.out[0].write([ev])
    
    def __call__(self):
        
        try:
            self.done = False
            while not self.done:
                # t = self.clock.tick(60)*0.001
                t = 0
                self.logic(t)
                if self.done:
                    break
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

