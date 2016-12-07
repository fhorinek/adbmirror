import socket
import struct
import errno

from subprocess import Popen
from glue import MyThread
from time import sleep

BANNER = 0
BANNER_SIZE = 24

HEAD = 1
HEAD_SIZE = 4

DATA = 2

class CapClient(MyThread):
    def __init__(self, parent):
        MyThread.__init__(self)
        
        disp_max = max(parent.size)
        dev_max = max(parent.orig)
        args = "-P %ux%u@%ux%u/0 -S -Q 80" % (dev_max, dev_max, disp_max, disp_max)
        cmd = ["adb", "shell", "LD_LIBRARY_PATH=%s %s/minicap %s" % (parent.path, parent.path, args)]
        self.server = Popen(cmd)
      
    def cut_data(self, size):
        tmp = self.data[:size]
        self.data = self.data[size:] 
        return tmp
        
    def run(self):
        sleep(1)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(("localhost", 1313))
        self.socket.setblocking(0)        
        
        self.running = True
        self.state = BANNER
        
        self.data = ""
    
        while self.running:
            for msg in self.internal_read():
                cmd = msg[0]
                if cmd == "end":
                    self.running = False
        
            try:
                data = self.socket.recv(1024 * 1024)
                self.data += data
            except socket.error, e:
                err = e.args[0]
                if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                    pass
                    
            if self.state == BANNER and len(self.data) >= BANNER_SIZE:
                banner_data = self.cut_data(BANNER_SIZE)
                self.banner = struct.unpack("<BBIIIIIBB", banner_data)
                self.state = HEAD
                print "Banner"
                print self.banner
                
            if self.state == HEAD and len(self.data) >= HEAD_SIZE:
                head_data = self.cut_data(HEAD_SIZE)
                self.data_size, = struct.unpack("<I", head_data)
                self.state = DATA

            if self.state == DATA and len(self.data) >= self.data_size:
                img_data = self.cut_data(self.data_size)
                self.internal_write(["data", img_data])
                self.state = HEAD
                    
            
        self.socket.close()
        self.server.kill()
