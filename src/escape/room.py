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
    FRONT_KEYPAD = 8


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
ROTATIONS[View.FRONT_KEYPAD] = {quad: View.FRONT_WALL for quad in Quadrant}


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


def font(size):
    return pygame.font.SysFont('couriernew', size, bold=True)


class _ChestBase(img.Factory):

    _CHARPOS: List[Tuple[int, int]] = None
    _FONT_SIZE: int = None

    _KEY = 'AYP'

    def __init__(self, names, screen, position, shift):
        super().__init__(screen)
        self._font = font(self._FONT_SIZE)
        self._images = [
            img.load(name, screen, position, shift) for name in names]
        self.text = ''

    @property
    def opened(self):
        return self.text == self._KEY

    def draw(self):
        self._images[self.opened].draw()
        if not self.opened:
            for c, pos in zip(self.text, self._CHARPOS):
                self._screen.blit(self._font.render(c, 0, color.BLACK), pos)

    def collidepoint(self, pos):
        return self._images[self.opened].collidepoint(pos)


class Chest(_ChestBase):

    _CHARPOS = [(496, 278), (509, 278), (521, 278)]
    _FONT_SIZE = 15

    def __init__(self, screen):
        super().__init__(('chest', 'chest_opened'), screen,
                         (RECT.w / 2, 2 * RECT.h / 3), (-0.5, -1))

    def send(self, event):
        """Sends an event that may be consumed as an unlocking input.
        event: An event.
        Returns:
          None if the event should not be consumed by the chest.
          False if the event is consumed but the chest should not be redrawn.
          True if the event is consumed and the chest should be redrawn.
        """
        if event.type != KEYDOWN or self.opened:
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
        super().__init__(('mini_chest', 'mini_chest_opened'), screen,
                         (RECT.w / 2, RECT.h * 7 / 8), (-0.5, -1))


class FrontDoor(img.Factory):

    _RECT = pygame.Rect(2 * RECT.w / 5, RECT.h / 4, RECT.w / 5, 3 * RECT.h / 4)
    _GAP = pygame.Rect(_RECT.right - 5, _RECT.top - 2, 10, _RECT.h + 2)

    _DIGITS = {
        '1': (570, 343),
        '2': (580, 343),
        '3': (589, 343),
        '4': (569, 355),
        '5': (579, 355),
        '6': (587, 355),
        '7': (569, 367),
        '8': (579, 367),
        '9': (587, 367),
        '0': (579, 378),
    }

    def __init__(self, screen):
        super().__init__(screen)
        self._door = img.load('door', screen, (RECT.w / 2, RECT.h), (-0.5, -1))

        ft = font(10)
        self._digits = tuple(ft.render(d, 0, color.BLACK) for d in self._DIGITS)

        self.revealed = False
        self.light_switch_on = True

    def draw(self):
        if self.revealed:
            self._door.draw()
            for i, pos in enumerate(self._DIGITS.values()):
                self._screen.blit(self._digits[i], pos)
            return
        if self.light_switch_on:
            gap_color = color.DARK_GREY_1
        else:
            gap_color = color.DARK_GREY_2
        pygame.draw.rect(self._screen, gap_color, self._RECT, 5)
        pygame.draw.rect(self._screen, gap_color, self._GAP)

    def collidepoint(self, pos):
        return (self._door if self.revealed else self._GAP).collidepoint(pos)


class LightSwitchBase(img.Factory):

    def __init__(self, names, screen, position, shift):
        assert len(names) == 2  # image names for off and on positions
        super().__init__(screen)
        self.on = True
        self._images = [
            img.load(name, screen, position, shift) for name in names]

    def draw(self):
        self._images[self.on].draw()

    def collidepoint(self, pos):
        return self._images[self.on].collidepoint(pos)


class LightSwitch(LightSwitchBase):

    def __init__(self, screen):
        super().__init__(('light_switch_off', 'light_switch_on'), screen,
                         (RECT.w / 2, RECT.h / 2), (-0.5, -1))


class MiniLightSwitch(LightSwitchBase):

    def __init__(self, screen):
        super().__init__(('mini_light_switch_off', 'mini_light_switch_on'),
                         screen, (RECT.w * 7 / 8, RECT.h / 2), (-0.5, -1))


class Images:

    def __init__(self, screen):
        self.chest = img.load(screen, factory=Chest)
        self.mini_chest = img.load(screen, factory=MiniChest)

        self.front_door = img.load(screen, factory=FrontDoor)

        self.front_keypad = img.load(
            'keypad', screen, (RECT.w / 2, 0), (-0.5, 0))

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
        self.mini_zodiac = img.load('mini_zodiac', screen)
