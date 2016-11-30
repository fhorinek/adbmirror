import time

from subprocess import Popen, PIPE
from glue import MyThread


class AdbClient(MyThread):
    def __init__(self):
        MyThread.__init__(self)
        
        cmd = ["adb", "shell"]
        self.app = Popen(cmd, stdin=PIPE)
        
        self.rot_auto(False)
        
    def cmd(self, cmd):
        self.app.stdin.write(cmd + "\n")
        self.app.stdin.flush()
        
    def rot_portrait(self):
        self.cmd("content insert --uri content://settings/system --bind name:s:user_rotation --bind value:i:0")
    
    def rot_landscape(self):
        self.cmd("content insert --uri content://settings/system --bind name:s:user_rotation --bind value:i:1")
    
    def rot_auto(self, auto):
        self.cmd("content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:%d" % int(bool(auto)))
      
    def press(self, key):
        self.cmd("input keyevent %s" % key);
    
        
    def run(self):
        self.running = True
        
        self.data = ""
    
        while self.running:
            for msg in self.internal_read():
                cmd = msg[0]
                if cmd == "end":
                    self.running = False
                    self.rot_auto(True)
                    time.sleep(1)
                    
                if cmd == "portrait":
                    self.rot_portrait()

                if cmd == "landscape":
                    self.rot_landscape()
                    
                if cmd == "home":
                    self.press("KEYCODE_HOME")

                if cmd == "back":
                    self.press("KEYCODE_BACK")

                if cmd == "apps":
                    self.press("KEYCODE_APP_SWITCH")

                if cmd == "power":
                    self.press("KEYCODE_POWER")
            
        self.app.kill()

