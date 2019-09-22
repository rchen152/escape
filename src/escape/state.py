"""Game state."""

import pygame
from pygame.locals import *


WINSIZE = (1024, 576)


def _keypressed(event, key):
    return event.type == KEYDOWN and event.key == key


class GameState:

    def __init__(self):
        self.active = True

    def handle_events(self, events):
        for event in events:
            self.handle_quit(event)
            self.handle_fullscreen(event)

    def handle_quit(self, event):
        if event.type == QUIT or _keypressed(event, K_q):
            self.active = False

    def handle_fullscreen(self, event):
        if not _keypressed(event, K_f):
            return
        if pygame.display.get_surface().get_flags() & FULLSCREEN:
            pygame.display.set_mode(WINSIZE)
        else:
            pygame.display.set_mode(WINSIZE, FULLSCREEN)
