"""Game room."""

import enum
import pygame
from pygame.locals import *
import string
from typing import List, Tuple
from . import color
from . import img


RECT = pygame.Rect(0, 0, 1024, 576)
BACK_WALL = pygame.Rect(RECT.w / 4, RECT.h / 4, RECT.w / 2, RECT.h / 2)


class View(enum.Enum):
    LEFT_WALL = 0
    CEILING = 1
    RIGHT_WALL = 2
    FLOOR = 3
    FRONT_WALL = 4
    BACK_WALL = 5
    DEFAULT = 6
    LEFT_WINDOW = 7


class Quadrant(enum.Enum):
    LEFT = 0
    TOP = 1
    RIGHT = 2
    BOTTOM = 3


ROTATIONS = {View.LEFT_WALL: {Quadrant.LEFT: View.FRONT_WALL.value,
                              Quadrant.RIGHT: View.BACK_WALL.value},
             View.CEILING: {Quadrant.TOP: View.FRONT_WALL.value,
                            Quadrant.BOTTOM: View.BACK_WALL.value},
             View.RIGHT_WALL: {Quadrant.LEFT: View.BACK_WALL.value,
                               Quadrant.RIGHT: View.FRONT_WALL.value},
             View.FLOOR: {Quadrant.TOP: View.BACK_WALL.value,
                          Quadrant.BOTTOM: View.FRONT_WALL.value}}
ROTATIONS[View.FRONT_WALL] = {quad: (2 - quad.value) % 4 for quad in Quadrant}
ROTATIONS[View.BACK_WALL] = ROTATIONS[View.DEFAULT] = {}
ROTATIONS[View.LEFT_WINDOW] = {quad: View.LEFT_WALL for quad in Quadrant}


def at_edge(pos):
    x, y = pos
    return x <= 5 or y <= 5 or RECT.w - x <= 5 or RECT.h - y <= 5


def quadrant(pos):
    x, y = pos
    if x == 0:
        # To avoid divide-by-zero, special-case the leftmost edge.
        return Quadrant.LEFT
    # Compute the (absolute values of) the slopes of the given position from the
    # top and bottom left corners of the screen.
    down_slope = y / x
    up_slope = (RECT.h - y) / x
    # Compute the slope of the screen.
    wall_slope = RECT.h / RECT.w
    # Determine the position relative to the screen diagonals.
    above_down_diagonal = down_slope < wall_slope
    above_up_diagonal = up_slope > wall_slope
    # The diagonals divide the screen into four quadrants. Use the relative
    # positions to determine which quadrant we're in.
    if not above_down_diagonal and above_up_diagonal:
        return Quadrant.LEFT
    if above_down_diagonal and above_up_diagonal:
        return Quadrant.TOP
    if above_down_diagonal and not above_up_diagonal:
        return Quadrant.RIGHT
    assert not above_down_diagonal and not above_up_diagonal
    return Quadrant.BOTTOM


class _ChestBase(img.PngFactory):

    _CHARPOS: List[Tuple[int, int]] = None
    _FONT_SIZE: int = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._font = pygame.font.SysFont(
            'couriernew', self._FONT_SIZE, bold=True)
        self.text = ''

    def draw(self):
        super().draw()
        for c, pos in zip(self.text, self._CHARPOS):
            self._screen.blit(self._font.render(c, 0, color.BLACK), pos)


class Chest(_ChestBase):

    _CHARPOS = [(496, 278), (509, 278), (521, 278)]
    _FONT_SIZE = 15

    def __init__(self, screen):
        super().__init__('chest', screen, (RECT.w / 2, RECT.h / 6), (-0.5, 0.5))

    def send(self, event):
        """Sends an event that may be consumed as an unlocking input.

        event: An event.

        Returns:
          None if the event should not be consumed by the chest.
          False if the event is consumed but the chest should not be redrawn.
          True if the event is consumed and the chest should be redrawn.
        """
        if event.type != KEYDOWN:
            return None
        if event.key == K_BACKSPACE:
            # Backspace is consumed as deletion of the rightmost character;
            # whether it requires a redraw depends on whether there exists a
            # character to delete.
            redraw = bool(self.text)
            self.text = self.text[:-1]
            return redraw
        if not event.unicode or event.unicode not in string.printable:
            # Aside from backspace, only printable characters are consumed.
            return None
        if len(self.text) >= 3:
            # We can't input more characters than there are dials on the lock.
            return False
        self.text += event.unicode
        return True


class MiniChest(_ChestBase):

    _CHARPOS = [(501, 430), (510, 430), (519, 430)]
    _FONT_SIZE = 10

    def __init__(self, screen):
        super().__init__(
            'mini_chest', screen, (RECT.w / 2, RECT.h * 7 / 8), (-0.5, -1))


class FrontDoor(img.Factory):

    _RECT = pygame.Rect(2 * RECT.w / 5, RECT.h / 4, RECT.w / 5, 3 * RECT.h / 4)
    _GAP = pygame.Rect(_RECT.right - 5, _RECT.top - 2, 10, _RECT.h + 2)
    _PANEL = pygame.Rect(_RECT.left + 2, _RECT.top + 2, 20, _RECT.h - 2)

    def __init__(self, screen):
        super().__init__(screen)
        self.revealed = False
        self.light_switch_on = True

    def draw(self):
        if self.light_switch_on:
            wall_color = color.GREY
            gap_color = color.DARK_GREY_1
        else:
            wall_color = gap_color = color.DARK_GREY_2
        if self.revealed:
            pygame.draw.rect(self._screen, color.BLACK, self._RECT)
            pygame.draw.rect(self._screen, gap_color, self._RECT, 5)
            pygame.draw.rect(self._screen, wall_color, self._PANEL)
        else:
            pygame.draw.rect(self._screen, gap_color, self._RECT, 5)
            pygame.draw.rect(self._screen, gap_color, self._GAP)

    def collidepoint(self, pos):
        return not self.revealed and self._GAP.collidepoint(pos)


class LightSwitch(img.Factory):
    """Temporary switch."""

    _RECT = pygame.Rect(480, 216, 64, 72)

    def __init__(self, screen):
        super().__init__(screen)
        self.on = True

    @property
    def color(self):
        return color.YELLOW if self.on else color.BLACK

    def draw(self):
        pygame.draw.rect(self._screen, self.color, self._RECT)

    def collidepoint(self, pos):
        return self._RECT.collidepoint(pos)


class MiniLightSwitch(img.Factory):
    """Temporary mini switch."""

    def __init__(self, screen):
        super().__init__(screen)
        self._rect = None
        self.on = True

    @property
    def color(self):
        return color.YELLOW if self.on else color.BLACK

    def draw(self):
        self._rect = pygame.draw.polygon(self._screen, self.color, [
            (888, 235), (904, 233), (904, 288), (888, 288)])

    def collidepoint(self, pos):
        return self._rect and self._rect.collidepoint(pos)


class Images:

    def __init__(self, screen):
        self.chest = img.load(screen, factory=Chest)
        self.mini_chest = img.load(screen, factory=MiniChest)

        self.front_door = img.load(screen, factory=FrontDoor)

        self.light_switch = img.load(screen, factory=LightSwitch)
        self.mini_light_switch = img.load(screen, factory=MiniLightSwitch)

        self.math = img.load('math', screen)
        self.mini_math = img.load('mini_math', screen, BACK_WALL.topleft)

        self.window = img.load(
            'window', screen, (RECT.w / 4, RECT.h / 2), (0, -1))
        self.mini_window = img.load(
            'mini_window', screen, (RECT.w / 16, RECT.h / 2), (0, -1))
        self.maxi_window = img.load('maxi_window', screen, (0, RECT.h / 4))

        self.zodiac = img.load('zodiac', screen)
