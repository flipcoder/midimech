import io
import struct
import glm
import time
import sys
import multiprocessing
from queue import Empty, Full

class LEDGridDisplay:
    def __init__(self, width=32, height=16):
        import xled
        self.WIDTH = width
        self.HEIGHT = height
        self.SIZE = width * height
        self.BMP = [None] * self.SIZE
        self.SCREEN = [glm.vec3(0, 0, 0) for _ in range(self.SIZE)]
        self.ORIENT = [0] * self.SIZE
        
        # Colors
        self.RED = glm.vec3(1, 0, 0)
        self.GREEN = glm.vec3(0, 1, 0)
        self.BLUE = glm.vec3(0, 0, 1)
        self.BLACK = glm.vec3(0, 0, 0)
        self.WHITE = glm.vec3(1, 1, 1)
        
        # Grid configuration
        self.GRID_SIZE = 8 # subgrid is always 8 on device
        self.GRIDS_WIDE = 4
        self.GRIDS_HIGH = 2
        self.NUM_GRIDS = self.GRIDS_WIDE * self.GRIDS_HIGH
        
        # Initialize device
        try:
            dev = xled.discover.discover()
            self.host = dev.ip_address
            print(f"Connected to device at {self.host}")
            self.ctr = xled.ControlInterface(self.host)
            self.ctr.set_mode("rt")
        except Exception as ex:
            print(ex)
        
        # Block configuration
        self.BLOCK_FLAGS = [None] * self.NUM_GRIDS
        for i in range(self.NUM_GRIDS):
            self.BLOCK_FLAGS[i] = set()
        self.LBLOCK = [0] * self.NUM_GRIDS
        self.PBLOCK = [0] * self.NUM_GRIDS
        self._setup_block_config()
        self._setup_orientations()


    def _setup_block_config(self):
    #     # Physical block flags
        self.BLOCK_FLAGS[0].add('h')
        self.BLOCK_FLAGS[1].add('h')
        self.BLOCK_FLAGS[2].add('h')
        self.BLOCK_FLAGS[3].add('h')
        self.BLOCK_FLAGS[4].add('v')
        self.BLOCK_FLAGS[5].add('v')
        self.BLOCK_FLAGS[6].add('v')
        self.BLOCK_FLAGS[7].add('h')
        
        # Logical to Physical block mapping
        self.PBLOCK[0] = 7
        self.PBLOCK[1] = 6
        self.PBLOCK[2] = 5
        self.PBLOCK[3] = 4
        self.PBLOCK[4] = 0
        self.PBLOCK[5] = 1
        self.PBLOCK[6] = 2
        self.PBLOCK[7] = 3

    def _setup_orientations(self):
        r = 0
        for lblock in range(8):
            pblock = self.PBLOCK[lblock]
            H = 'h' in self.BLOCK_FLAGS[pblock]
            V = 'v' in self.BLOCK_FLAGS[pblock]
            for i in range(64):
                x = i % 8
                y = i // 8
                flip_row = (y % 2 == 0)
                if H:
                    flip_row = not flip_row
                if V:
                    flip_row = not flip_row
                if flip_row:
                    self.ORIENT[r] = (pblock * 64) + (x + (8 * (7-y)) if V else x + (8 * y))
                else:
                    self.ORIENT[r] = (pblock * 64) + ((7-x) + (8 * (7-y)) if V else (7-x) + (8 * y))
                r += 1

    def encode_frame(self, frame):
        for i in range(self.SIZE):
            px = frame[i]
            r = glm.clamp(int(px[0] * 255), 0, 255)
            g = glm.clamp(int(px[1] * 255), 0, 255)
            b = glm.clamp(int(px[2] * 255), 0, 255)
            self.BMP[i] = struct.pack(">BBB", r, g, b)
        frame_io = io.BytesIO()
        frame_io.write(b"".join(self.BMP))
        frame_io.seek(0)
        return frame_io

    def clear(self, color):
        for i in range(self.SIZE):
            self.SCREEN[i] = color

    def draw(self):
        frame = self.encode_frame(self.SCREEN)
        self.ctr.set_rt_frame_rest(frame)

    def transform(self, i):
        total_width = self.GRIDS_WIDE * self.GRID_SIZE
        global_x = i % total_width
        global_y = i // total_width
        grid_num_x = global_x // self.GRID_SIZE
        grid_num_y = global_y // self.GRID_SIZE
        grid_num = grid_num_y * self.GRIDS_WIDE + grid_num_x
        local_x = global_x % self.GRID_SIZE
        local_y = global_y % self.GRID_SIZE
        grid_index = local_y * self.GRID_SIZE + local_x
        return grid_index + 64 * grid_num

    def transform_xy(self, x, y):
        p = self.transform(x + (y * self.WIDTH))
        return glm.ivec2(p % self.WIDTH, p // self.WIDTH)

    # def put(self, color, x, y):
    #     if y < 0 or y >= self.HEIGHT:
    #         return
    #     if x < 0 or x >= self.WIDTH:
    #         return
    #     i = x + (y * self.WIDTH)
    #     ii = self.ORIENT[self.transform(i)]
    #     self.SCREEN[ii] = color

    def put(self, color, x, y, size=1):
        x *= size
        y *= size
        for yofs in range(size):
            for xofs in range(size):
                if y < 0 or y >= self.HEIGHT:
                    continue
                if x < 0 or x >= self.WIDTH:
                    continue
                i = x + xofs + (y+yofs) * self.WIDTH
                try:
                    ii = self.ORIENT[self.transform(i)]
                except Exception as ex:
                    continue
                self.SCREEN[ii] = color

    def test_pattern(self):
        # Print coordinate mapping
        # for j in range(self.HEIGHT):
        #     for i in range(self.WIDTH):
        #         t = self.transform_xy(i, j)
        #         print(f"{i},{j} {t.x},{t.y}", end=' ')
        #     print()

        # Test display
        for i in range(self.SIZE):
            pos = glm.ivec2(i % self.WIDTH, i // self.WIDTH)
            self.clear(self.BLACK)
            self.put(self.RED, pos.x, pos.y)
            self.draw()
            # time.sleep(0.001)

#     display = LEDGridDisplay(width, height)

#     last_draw_time = 0
#     DRAW_INTERVAL = 0.25
#     dirty = False

#     while True:
#         try:
#             command, args = command_queue.get(timeout=0.1)
#             if command == "put":
#                 display.put(*args)
#             elif command == "clear":
#                 display.clear(*args)
#             elif command == "draw":
#                 # Ignore explicit draw commands; we'll handle it in the loop
#                 dirty = True

#             # Check if it's time to draw
#             if dirty:
#                 current_time = time.time()
#                 if current_time - last_draw_time >= DRAW_INTERVAL:
#                     display.draw()
#                     last_draw_time = current_time
#                     dirty = False

#         except Empty:
#             # Still check for drawing even if queue is empty
#             if dirty:
#                 current_time = time.time()
#                 if current_time - last_draw_time >= DRAW_INTERVAL:
#                     display.draw()
#                     last_draw_time = current_time
#                     dirty = False
#             time.sleep(0.01)  # Avoid busy-waiting
#         except Exception as e:
#             print(f"Worker: Error processing command: {e}")
#             # last_draw_time = time.time()

#     # Process commands from the queue
#     while True:
#         try:
#             command, args = command_queue.get(timeout=1)
#             if command == "put":
#                 display.put(*args)
#             elif command == "clear":
#                 display.clear(*args)
#             elif command == "draw":
#                 display.draw()
#         except Empty:
#             continue

# class LEDGridInterface:
#     def __init__(self, width=24, height=16):
#         self.command_queue = multiprocessing.Queue(maxsize=10)
#         self.process = multiprocessing.Process(
#             target=led_grid_worker,
#             args=(self.command_queue, width, height),
#             daemon=True
#         )
#         self.process.start()
#         time.sleep(1)

#     def put(self, color, x, y):
#         try:
#             self.command_queue.put(("put", (color, x, y)))
#         except Full:
#             return False
#         return True

#     def clear(self, color):
#         try:
#             self.command_queue.put(("clear", (color,)))
#         except Full:
#             return False
#         return True

#     def draw(self):
#         try:
#             self.command_queue.put(("draw", ()))
#         except Full:
#             return False
#         return True

# Example usage
if __name__ == "__main__":
    # Create the interface
    display = LEDGridDisplay()

    # Test pattern equivalent
    RED = glm.vec3(1, 0, 0)
    BLACK = glm.vec3(0, 0, 0)
    WHITE = glm.vec3(1, 1, 1)

    for i in range(24 * 16):  # SIZE = WIDTH * HEIGHT
        pos = glm.ivec2(i % 24, i // 24)
        display.clear(BLACK)
        display.put(RED, pos.x, pos.y)
        display.draw()
        time.sleep(0.001)  # Small delay to simulate original timing

    display.clear(WHITE)
    display.draw()

    # Give some time for the process to handle commands
    time.sleep(1)
    print("Main process done")

