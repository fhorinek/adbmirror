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

class Main():
    def __init__(self):
        assert len(sys.argv) == 4
        self.size = map(int, sys.argv[1].split("x"))
        self.proj = list(self.size)
        orig = map(int, sys.argv[2].split("x"))
        self.orig = orig[1], orig[0]
        self.path = sys.argv[3]
        
        self.scalel = True
        self.scalep = True
        
        self.cap = CapClient(self)
        self.cap.start()
        
        self.touch = TouchClient(self)
        self.touch.start()
        
        self.rot = RotationClient()
        self.rot.start()
        
        self.adb = AdbClient()
        self.adb.start()
        
        self.mouse_down = False
        self.mouse_down_time = 0
        self.mouse_inmenu = False
        
        self.show_menu = False
        self.show_menu_time = 0

        self.show_nav = False

        self.calc_scale()

        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode(self.size)
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
        if self.show_nav:
            self.proj[0] = self.size[0] - self.nav_w
        else:
            self.proj[0] = self.size[0]

    
        m = self.orig[0] / float(self.size[0])
        self.sizel = self.size[0], int(self.orig[1] / m)
        self.sizep = int(self.orig[1] / m), self.size[0]

        #landscape
        self.ly = int((self.size[1] - self.sizel[1]) / 2)
        

        
    def blit_center(self, dst, src, rect):
        x = rect[0] - int((src.get_width() / 2) - (rect[2] / 2))
        y = rect[1] - int((src.get_height() / 2) - (rect[3] / 2))
        dst.blit(src, (x, y)) 
        
    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
                self.cap.write(["end"])
                self.touch.write(["end"])
                self.rot.write(["end"])
                self.adb.write(["end"])
               
               
            if hasattr(event, "pos"):
                ix, iy = event.pos
                self.mouse_inmenu = ix <= self.size[1] * MENU_BORDER / 100.0
                
                if self.rotation == 90:
                    y = (ix / float(self.size[0]))
                    if self.scalel:
                        x = 1.0 - (iy / float(self.size[1]))
                    else:
                        x = 1.0 - (((iy - self.yl)) / float(self.sizel[1]))

                if self.rotation == 270:
                    y = 1.0 - (ix / float(self.size[0]))
                    if self.scalel:
                        x = (iy / float(self.size[1]))
                    else:
                        x = (((iy - self.yl)) / float(self.sizel[1]))

                if self.rotation == 0:
                    y = iy / float(self.size[1])
                    if self.scalep:
                        x = ix  / float(self.size[0])
                    else:
                        x = ((ix - self.xp)) / float(self.sizep[0])

                if self.rotation == 180:
                    y = 1.0 - (iy / float(self.size[1]))
                    if self.scalep:
                        x = 1.0 - (ix  / float(self.size[0]))
                    else:
                        x = 1.0 - (((ix - self.xp)) / float(self.sizep[0]))
                           
                x = min(max(0, x), 1)
                y = min(max(0, y), 1)
                print x, y
            
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
                        self.mouse_down_time = time()
                
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
        self.screen_update = True        
    
          
    def menu_loop(self):
        if self.mouse_down and time() - self.mouse_down_time > MENU_TAP and self.mouse_inmenu:
            self.show_menu = True
            self.screen_update = True
            self.show_menu_time = time()

        if self.show_menu and time() - self.show_menu_time > MENU_TIMEOUT:
            self.show_menu = False
            self.screen_update = True
        
        
    def run(self):
        self.running = True
        self.rotation = 0
        self.adb.write(["landscape"])

        self.screen_update = True
        screen_frame = pygame.Surface(self.size)
        
        while self.running:
            self.events()
 
            for msg in self.rot.read():
                cmd = msg[0]
                if cmd == "rot":
                    self.rotation = msg[1]
                    screen_frame.fill((0, 0, 0))
            
            for msg in self.cap.read():
                cmd = msg[0]
                if cmd == "head":
                    self.banner = msg[1]

                if cmd == "data":
                    data = cStringIO.StringIO(msg[1])
                    a = pygame.image.load(data)
                    self.screen_update = True
                    
                    landscape = self.rotation in [90, 270]
                    if landscape:       
                        a = a.subsurface(pygame.Rect((0,0), self.sizel))
                        if self.scalel:
                            a = pygame.transform.smoothscale(a, self.proj)
                            screen_frame.blit(a, (0, 0))
                    else:
                        a = a.subsurface(pygame.Rect((0,0), self.sizep))
                        if self.scalep:
                            a = pygame.transform.smoothscale(a, self.proj)
                            screen_frame.blit(a, (0, 0))
                    
                   
            self.menu_loop()
                        
            if self.screen_update:
                self.screen_update = False
                self.screen.blit(screen_frame, (0, 0))
                if self.show_menu:
                    self.screen.blit(self.img_menu, (0, 0))
                if self.show_nav:
                    self.screen.blit(self.img_nav, (self.size[0] - self.nav_w, 0))
                pygame.display.update()
                        

             
a = Main()
a.run()
