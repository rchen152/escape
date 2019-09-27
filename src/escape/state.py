"""Game state."""

import abc
import pygame
from pygame.locals import *
import os
from . import room


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
            pygame.display.set_mode(room.RECT.size)
        else:
            pygame.display.set_mode(room.RECT.size, FULLSCREEN)
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
        img = pygame.transform.scale(img.convert_alpha(), room.RECT.size)
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

    def __init__(self, screen):
        self.view = room.View.DEFAULT
        super().__init__(screen)

    def _draw_default(self):
        self.screen.fill(_GREY)
        pygame.draw.rect(self.screen, _BLACK, room.BACK_WALL, 5)
        for corner in ('topleft', 'bottomleft', 'bottomright', 'topright'):
            pygame.draw.line(self.screen, _BLACK, getattr(room.RECT, corner),
                             getattr(room.BACK_WALL, corner), 5)
        pygame.display.update()

    def draw(self):
        if self.view is room.View.DEFAULT:
            self._draw_default()
        else:
            self.screen.fill(_GREY)
            font = pygame.font.Font(None, 80)
            text = self.view.name
            size = font.size(text)
            ren = font.render(text, 0, _BLACK, _GREY)
            self.screen.blit(
                ren, ((room.RECT.w - size[0]) / 2, (room.RECT.h - size[1]) / 2))
            pygame.display.update()

    def _handle_default_click(self, pos):
        if room.at_edge(pos):
            # In the default view, the edges of the screen border the (hidden)
            # front wall.
            self.view = room.View.FRONT_WALL
            return
        if room.BACK_WALL.collidepoint(pos):
            # The back wall is a rectangle, so use built-in collision detection.
            self.view = room.View.BACK_WALL
            return
        # Since we've already checked the front and back walls, the quadrant
        # corresponds to one of the other four walls.
        self.view = room.View(room.quadrant(pos).value)

    def handle_click(self, event):
        if event.type != MOUSEBUTTONUP or event.button != 1:
            return False
        if self.view is room.View.DEFAULT:
            self._handle_default_click(event.pos)
        elif not room.at_edge(event.pos):
            return False
        else:
            quadrant = room.quadrant(event.pos)
            self.view = room.View(
                room.ROTATIONS[self.view].get(quadrant, quadrant.value))
        self.draw()
        return True

    def handle_reset(self, event):
        if not _keypressed(event, K_r):
            return False
        if self.view is not room.View.DEFAULT:
            self.view = room.View.DEFAULT
            self.draw()
        return True
