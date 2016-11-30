import fcntl
import os

from subprocess import Popen, PIPE
from glue import MyThread


class RotationClient(MyThread):
    def __init__(self):
        def setNonBlocking(fd):
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            flags = flags | os.O_NONBLOCK
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)
        
        MyThread.__init__(self)
        
        cmd = ["adb", "shell", "pm path jp.co.cyberagent.stf.rotationwatcher"]
        out, __ = Popen(cmd, stdout = PIPE).communicate()
        apk_path = out.split(":")[1].split()[0]
        
        cmd = ["adb", "shell", "CLASSPATH='%s' exec app_process /system/bin jp.co.cyberagent.stf.rotationwatcher.RotationWatcher" % (apk_path)]
        self.app = Popen(cmd, stdout= PIPE)
        setNonBlocking(self.app.stdout)
        
    def cut_data(self, size):
        tmp = self.data[:size]
        self.data = self.data[size:]
        return tmp
        
    def run(self):
        self.running = True
        
        self.data = ""
    
        while self.running:
            for msg in self.internal_read():
                cmd = msg[0]
                if cmd == "end":
                    self.running = False

            try:
                self.data += self.app.stdout.read().replace("\r\n", "\n")
           
            except IOError:
                continue
            
            while '\n' in self.data:
                data = self.cut_data(self.data.find('\n') + 1).split()[0]
                self.internal_write(["rot", int(data)])
            
        self.app.kill()

