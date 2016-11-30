import socket
import errno

from subprocess import Popen
from glue import MyThread
from time import sleep

class TouchClient(MyThread):
    def __init__(self, parent):
        MyThread.__init__(self)
        
        cmd = ["adb", "shell", " %s/minitouch" % (parent.path)]
        self.server = Popen(cmd)
        
        self.pressure = 0
        self.max_x = 0
        self.max_y = 0

    def cut_data(self, size):
        tmp = self.data[:size]
        self.data = self.data[size:]
        return tmp
        
    def send(self, data):
        data += "\nc\n";
        self.socket.sendall(data)
        
    def run(self):
        sleep(1)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 1111))
        self.socket.setblocking(0)
        
        self.running = True
        self.data = ""
    
        while self.running:
            for msg in self.internal_read():
                cmd = msg[0]
                if cmd == "end":
                    self.running = False

                if cmd == "down":
                    x = int(msg[1] * self.max_x)
                    y = int(msg[2] * self.max_y)
                    self.send("d 0 %u %u %u" % (x, y, self.pressure))

                if cmd == "up":
                    self.send("u 0")
               
                if cmd == "move":
                    x = int(msg[1] * self.max_x)
                    y = int(msg[2] * self.max_y)
                    self.send("m 0 %u %u %u" % (x, y, self.pressure))
        
            try:
                data = self.socket.recv(1024)
                self.data += data
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    pass
            
            while '\n' in self.data:
                data = self.cut_data(self.data.find('\n') + 1)
                data = data.split()
                
                if data[0] is 'v':
                    self.version = int(data[1])

                if data[0] is '$':
                    self.pid = int(data[1])

                if data[0] is '^':
                    self.max_x = int(data[2])
                    self.max_y = int(data[3])
                    self.pressure = int(data[4])
            
        self.socket.close()
        self.server.kill()
