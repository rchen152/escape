"""Game state."""

import abc
import pygame
from pygame.locals import *
import os


WINRECT = pygame.Rect(0, 0, 1024, 576)

_BLACK = (0, 0, 0)
_GREY = (200, 200, 200)
_RED = (200, 25, 25)


def _keypressed(event, key):
    return event.type == KEYDOWN and event.key == key


class GameState(abc.ABC):
    """Base class for tracking game state.

    run() checks the event queue in a loop until a quit event is received. For
    each event, every handle_* method is called until the event is consumed. A
    handler reports that it consumed an event by returning True.
    """

    def __init__(self, screen):
        self.screen = screen
        self.active = True
        self.draw()
        self._event_handlers = [
            getattr(self, x) for x in dir(self) if x.startswith('handle_')]

    @abc.abstractmethod
    def draw(self):
        pass

    def cleanup(self):
        pass

    def handle_quit(self, event):
        if event.type == QUIT or _keypressed(event, K_q):
            self.active = False
            return True
        return False

    def handle_fullscreen(self, event):
        if not _keypressed(event, K_f):
            return False
        if self.screen.get_flags() & FULLSCREEN:
            pygame.display.set_mode(WINRECT.size)
        else:
            pygame.display.set_mode(WINRECT.size, FULLSCREEN)
        self.draw()
        return True

    def run(self):
        while self.active:
            for event in pygame.event.get():
                for handle in self._event_handlers:
                    consumed = handle(event)
                    if consumed:
                        break
        self.cleanup()


class TitleCard(GameState):

    _TIMED_QUIT = pygame.USEREVENT
    _DISPLAY_TIME_MS = 5000

    def __init__(self, screen):
        super().__init__(screen)
        pygame.time.set_timer(self._TIMED_QUIT, self._DISPLAY_TIME_MS)

    def draw(self):
        path = os.path.join(os.path.dirname(__file__), 'img', 'title_card.png')
        img = pygame.image.load(path)
        img = pygame.transform.scale(img.convert_alpha(), WINRECT.size)
        self.screen.fill(_RED)
        self.screen.blit(img, (0, 0))
        pygame.display.update()

    def handle_quit(self, event):
        if event.type == self._TIMED_QUIT:
            self.active = False
            return True
        return super().handle_quit(event)

    def cleanup(self):
        pygame.time.set_timer(self._TIMED_QUIT, 0)


class Game(GameState):

    def draw(self):
        self.screen.fill(_GREY)
        x = WINRECT.width / 4
        y = WINRECT.height / 4
        w = WINRECT.width / 2
        h = WINRECT.height / 2
        back_wall = pygame.draw.rect(self.screen, _BLACK, (x, y, w, h), 5)
        for corner in ('topleft', 'bottomleft', 'bottomright', 'topright'):
            pygame.draw.line(self.screen, _BLACK, getattr(WINRECT, corner),
                             getattr(back_wall, corner), 5)
        pygame.display.update()
