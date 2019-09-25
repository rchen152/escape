"""Game state."""

import abc
import pygame
from pygame.locals import *
import os


WINSIZE = (1024, 576)
_RED = (200, 25, 25)
_BLACK = (0, 0, 0)


def _keypressed(event, key):
    return event.type == KEYDOWN and event.key == key


class GameState(abc.ABC):

    def __init__(self, screen):
        self.screen = screen
        self.active = True
        self.draw()

    @abc.abstractmethod
    def draw(self):
        pass

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
        if self.screen.get_flags() & FULLSCREEN:
            pygame.display.set_mode(WINSIZE)
        else:
            pygame.display.set_mode(WINSIZE, FULLSCREEN)
        self.draw()

    def run(self):
        while self.active:
            self.handle_events(pygame.event.get())


class TitleCard(GameState):

    def draw(self):
        path = os.path.join(os.path.dirname(__file__), 'img', 'title_card.png')
        img = pygame.image.load(path)
        img = pygame.transform.scale(img.convert_alpha(), WINSIZE)
        self.screen.fill(_RED)
        self.screen.blit(img, (0, 0))
        pygame.display.update()


class Game(GameState):

    def draw(self):
        self.screen.fill(_BLACK)
        pygame.display.update()
