import threading
from multiprocessing import Pipe

class MyThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.pipe_ext, self.pipe_int = Pipe()
            
    def read(self):
        msgs = []
        while self.pipe_ext.poll():
            msgs.append(self.pipe_ext.recv())
            
        return msgs

    def write(self, data):
        self.pipe_ext.send(data)
        
    
    def internal_read(self):
        msgs = []
        while self.pipe_int.poll():
            msgs.append(self.pipe_int.recv())
            
        return msgs

    def internal_write(self, data):
        self.pipe_int.send(data)

        
    