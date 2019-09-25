"""Game state."""

import abc
import pygame
from pygame.locals import *
import os


WINRECT = pygame.Rect(0, 0, 1024, 576)
_BACK_WALL = pygame.Rect(
    WINRECT.w / 4, WINRECT.h / 4, WINRECT.w / 2, WINRECT.h / 2)

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
        pygame.draw.rect(self.screen, _BLACK, _BACK_WALL, 5)
        for corner in ('topleft', 'bottomleft', 'bottomright', 'topright'):
            pygame.draw.line(self.screen, _BLACK, getattr(WINRECT, corner),
                             getattr(_BACK_WALL, corner), 5)
        pygame.display.update()

    def handle_click(self, event):
        """Determines which wall was clicked."""
        if event.type != MOUSEBUTTONUP or event.button != 1:
            return False
        if _BACK_WALL.collidepoint(event.pos):
            # The back wall is a rectangle, so use built-in collision detection.
            print('back wall')
            return True
        x, y = event.pos
        if x == 0:
            # To avoid divide-by-zero, special-case the leftmost edge.
            print('left wall')
            return True
        # Compute the (absolute values of) the slope of the current position
        # from the top left and bottom left corners of the screen and the slope
        # of the screen itself.
        down_slope = y / x
        up_slope = (WINRECT.h - y) / x
        # Compute the slope of the screen.
        wall_slope = WINRECT.h / WINRECT.w
        # Determine the position relative to the screen diagonals.
        above_down_diagonal = down_slope < wall_slope
        above_up_diagonal = up_slope > wall_slope
        # The diagonals divide the screen into four triangles. Use the relative
        # positions to determine which triangle we're in. Since we've already
        # checked the back wall, the triangle corresponds to one of the other
        # four walls.
        if not above_down_diagonal and above_up_diagonal:
            print('left wall')
            return True
        if above_down_diagonal and above_up_diagonal:
            print('ceiling')
            return True
        if above_down_diagonal and not above_up_diagonal:
            print('right wall')
            return True
        assert not above_down_diagonal and not above_up_diagonal
        print('floor')
        return True
