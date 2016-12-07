import pygame
import cStringIO
import sys
from time import time

from capclient import CapClient
from touchclient import TouchClient
from rotationclient import RotationClient
from adbclient import AdbClient

MENU_TAP = 2
MENU_TIMEOUT = 10
MENU_BORDER = 10
MENU_WIDTH = 15

NAV_WIDTH = 7

DOUBLECLICK_TIME = 0.2

class Main():
    def __init__(self):
        assert len(sys.argv) == 4
        self.size = map(int, sys.argv[1].split("x"))
        orig = map(int, sys.argv[2].split("x"))
        self.orig = orig[1], orig[0]
        self.path = sys.argv[3]
        
        self.scalel = True
        self.scalep = False
        
        self.cap = CapClient(self)
        self.cap.start()
        
        self.touch = TouchClient(self)
        self.touch.start()
        
        self.rot = RotationClient()
        self.rot.start()
        
        self.adb = AdbClient()
        self.adb.start()
        
        self.mouse_down = False
        self.mouse_time = 0
        self.mouse_inmenu = False
        
        self.show_menu = False
        self.show_menu_time = 0

        self.show_nav = False

        #image scale orig to disp
        self.scale = self.orig[0] / float(self.size[0])
        self.ratio = self.orig[0] / float(self.orig[1])
        #size of raw image in landscape mode
        self.sizel = self.size[0], int(self.orig[1] / self.scale)
        #size of raw image in portrait mode
        self.sizep = int(self.orig[1] / self.scale), self.size[0]

        self.rotation = 0

        self.calc_scale()

        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode(self.size, pygame.FULLSCREEN | pygame.HWSURFACE)
        pygame.display.set_caption("adbmirror")
 
        self.color = (200, 200, 200)
        
        font = pygame.font.Font("res/fontawesome.ttf", 70)
        img_portrait = font.render(u'\uf10b', True, self.color)
        img_landscape = pygame.transform.rotate(img_portrait, 90)
        img_bars = font.render(u'\uf0c9', True, self.color)
        
        font = pygame.font.Font("res/fontawesome.ttf", 30)
        img_back = font.render(u'\uf053', True, self.color)
        img_home = font.render(u'\uf015', True, self.color)
        img_box = font.render(u'\uf009', True, self.color)
        
        self.menu_w = int(self.size[0] * MENU_WIDTH / 100.0)
        self.menu_h = int(self.size[1] / 3)
        self.img_menu = pygame.Surface((self.menu_w, self.size[1]))
        
        self.blit_center(self.img_menu, img_portrait, (0, 0, self.menu_w, self.menu_h))
        self.blit_center(self.img_menu, img_landscape, (0, self.menu_h, self.menu_w, self.menu_h))
        self.blit_center(self.img_menu, img_bars, (0, self.menu_h * 2, self.menu_w, self.menu_h))
        
        self.nav_w = int(self.size[0] * NAV_WIDTH / 100.0)
        
        self.img_nav = pygame.Surface((self.nav_w, self.size[1]))
        self.blit_center(self.img_nav, img_box, (0, 0, self.nav_w, self.menu_h))
        self.blit_center(self.img_nav, img_home, (0, self.menu_h, self.nav_w, self.menu_h))
        self.blit_center(self.img_nav, img_back, (0, self.menu_h * 2, self.nav_w, self.menu_h))

    def calc_scale(self):
        self.landscape = self.rotation in [90, 270]
        
        if self.show_nav:
            max_w = self.size[0] - self.nav_w      
        else:            
            max_w = self.size[0]
 
        if self.landscape:
            x = 0
            w = max_w 
            if self.scalel:
                h = self.size[1]
                y = 0
            else:
                h = w / self.ratio
                y = (self.size[1] - h) / 2
        else:
            y = 0
            h = self.size[1]
            if self.scalep:
                x = 0
                w = max_w
            else:
                w = h / self.ratio
                x = (self.size[0] - w) / 2
                
        self.proj = map(int, [x, y, w, h]) 
        self.frame_update = True
        
    def blit_center(self, dst, src, rect):
        x = rect[0] - int((src.get_width() / 2) - (rect[2] / 2))
        y = rect[1] - int((src.get_height() / 2) - (rect[3] / 2))
        dst.blit(src, (x, y)) 
        
    def exit(self):
        self.running = False
        
        self.cap.write(["end"])
        self.touch.write(["end"])
        self.rot.write(["end"])
        self.adb.write(["end"])        
        
    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exit()
               
            if hasattr(event, "pos"):
                ix, iy = event.pos
                self.mouse_inmenu = ix <= self.size[1] * MENU_BORDER / 100.0
                
                fx = min(max(0, (ix - self.proj[0]) / float(self.proj[2])), 1)
                fy = min(max(0, (iy - self.proj[1]) / float(self.proj[3])), 1)

                if self.rotation == 0:
                    x = fx
                    y = fy

                if self.rotation == 90:
                    x = 1.0 - fy
                    y = fx
                    
                if self.rotation == 180:
                    x = 1.0 - fx
                    y = 1.0 - fy   
                
                if self.rotation == 270:
                    x = fy
                    y = 1.0 - fx                                 
            
            if hasattr(event, "button"):
                if event.button is not 1:
                    continue
                  
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if ix < self.menu_w and self.show_menu:
                        self.menu_action(iy / (self.size[1] / 3))
                    elif ix > self.size[0] - self.nav_w and self.show_nav:
                        self.nav_action(iy / (self.size[1] / 3))
                    else:
                        self.touch.write(["down", x, y])
                        self.mouse_down = True
                        self.mouse_time = time()
                
                if event.type == pygame.MOUSEBUTTONUP:
                    self.touch.write(["up"])
                    self.mouse_down = False
   
            if event.type == pygame.MOUSEMOTION:
                if self.mouse_down:
                    self.touch.write(["move", x, y])
                    

    def nav_action(self, but):
        if but == 0:
            self.adb.write(["apps"])
        if but == 1:
            self.adb.write(["home"])
        if but == 2:
            self.adb.write(["back"])


    def menu_action(self, but):
        if but == 0:
            self.adb.write(["portrait"])
        if but == 1:
            self.adb.write(["landscape"])
        if but == 2:
            self.show_nav = not self.show_nav
            self.calc_scale()

            
        self.show_menu = False
          
    def menu_loop(self):
        if self.mouse_down and time() - self.mouse_time > MENU_TAP and self.mouse_inmenu:
            self.show_menu = True
            self.screen_update = True
            self.show_menu_time = time()

        if self.show_menu and time() - self.show_menu_time > MENU_TIMEOUT:
            self.show_menu = False
            self.screen_update = True
    
    def run(self):
        self.running = True
        self.adb.write(["landscape"])

        self.screen_update = True
        self.frame_update = False
        
        frame_cache = pygame.Surface(self.size)
        last_frame = None
        
        while self.running:
            self.events()
 
            for msg in self.rot.read():
                cmd = msg[0]
                if cmd == "rot":
                    self.rotation = msg[1]
                    self.calc_scale()

            #we will process only one frame at the time
            msgs = self.cap.read()
            msgl = len(msgs)
            if msgl:
                msg = msgs[msgl - 1]
                cmd = msg[0]

                if cmd == "data":
                    data = cStringIO.StringIO(msg[1])
                    last_frame = pygame.image.load(data)
                    self.frame_update = True

            for msg in self.adb.read():
                cmd = msg[0]
                if cmd == "end":
                    self.exit()

            self.menu_loop()
                    
            if self.frame_update:
                self.frame_update = False
                
                if last_frame is not None:
                    if self.landscape:       
                        a = last_frame.subsurface(pygame.Rect((0,0), self.sizel))
                    else:
                        a = last_frame.subsurface(pygame.Rect((0,0), self.sizep))

                    aw, ah = a.get_size()
                    if aw != self.proj[2] or ah != self.proj[3]:
                    	frame_cache = pygame.transform.smoothscale(a, (self.proj[2], self.proj[3]))
                    else:
                        frame_cache = a.copy()

                self.screen_update = True
                        
            if self.screen_update:
                self.screen.fill((0, 0, 0))   
                self.screen_update = False
                self.screen.blit(frame_cache, (self.proj[0], self.proj[1]))   
                if self.show_menu:
                    self.screen.blit(self.img_menu, (0, 0))
                if self.show_nav:
                    self.screen.blit(self.img_nav, (self.size[0] - self.nav_w, 0))
                pygame.display.update()
                        

             
a = Main()
a.run()
