import threading
from Queue import Queue

class MyThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.q_in = Queue()
        self.q_out = Queue()
            
    def read(self):
        msgs = []
        try:
            while True:
                msgs.append(self.q_out.get(False))
   	finally:
            return msgs
            
        return msgs

    def write(self, data):
        self.q_in.put(data)
    
    def internal_read(self):
        msgs = []
        try:
            while True:
                msgs.append(self.q_in.get(False))
   	finally:
            return msgs

    def internal_write(self, data):
        self.q_out.put(data)

