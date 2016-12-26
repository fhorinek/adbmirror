import serial
import Xlib.display
from subprocess import Popen, PIPE
        

class SerialTouch():
    def __init__(self):
        res = Xlib.display.Display().screen().root.get_geometry()
        self.w = res.width
        self.h = res.height
        self.p = Popen("/usr/bin/xte", stdin=PIPE)

        self.down = False
        
        self.state = 0
        
        self.min_x = 63081
        self.max_x = 65449
        self.min_y = 63480
        self.max_y = 65402
        
        self.simulate = False
        if not self.simulate:
            port = "/dev/ttyS3"
            speed = 38400
            self.serial = serial.Serial(port, speed, timeout=0)
        
    def cmd(self, cmd):
        self.p.stdin.write(cmd + "\n")
        self.p.stdin.flush()
        

    def decode(self, data):
        if data[1] == 2: #touch
            raw_x = (data[3] << 8) + data[2]
            raw_y = (data[5] << 8) + data[4]
    
            x = int(self.w * (1.0 - (raw_x - self.min_x) / float(self.max_x - self.min_x)))
            y = int(self.h * (1.0 - (raw_y - self.min_y) / float(self.max_y - self.min_y)))
            self.cmd("mousemove %u %u" % (x, y))
            if not self.down:
                self.down = True
                self.cmd("mousedown 1")
    
        if data[1] == 3: #up
            self.down = False
            self.cmd("mouseup 1")
               
        
    def get_data(self):
        if self.simulate:
            f = open("/media/horinek/0236BEDB25E0CD79/fabia_touchscreen/raw.bin", "rb")
            data = f.read()
            f.close()
            self.running = False
        else:
            data = self.serial.read(1024)
        return data

    def loop(self):
        self.running = True
        while self.running:
            for d in self.get_data():
                c = ord(d)
                
                if self.state == 0:
                    if c == 16:
                        self.state = 1
                        continue
                    
                if self.state == 1:
                    if c == 141:
                        self.state = 2
                    else:
                        self.state = 0
                    continue
                
                if self.state == 2:
                    packet_len = c
                    self.state = 3
                    continue
                
                if self.state == 3:
                    packet_type = c
                    self.state = 4
                    data = [packet_len, packet_type]
                    continue
                
                if self.state == 4:
                    data.append(c)
                    packet_len -= 1
                    if packet_len == 0:
                        self.decode(data)
                        self.state = 0
        
        self.p.stdin.close()               
        self.p.wait()
        
T = SerialTouch()
T.loop()
