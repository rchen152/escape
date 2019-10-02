"""Game room."""

import enum
import pygame
from . import img


RECT = pygame.Rect(0, 0, 1024, 576)
BACK_WALL = pygame.Rect(RECT.w / 4, RECT.h / 4, RECT.w / 2, RECT.h / 2)
FRONT_DOOR = pygame.Rect(2 * RECT.w / 5, RECT.h / 4, RECT.w / 5, 3 * RECT.h / 4)


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


class Images:

    def __init__(self, screen):
        self.chest = img.load(
            'chest', screen, (RECT.w / 2, RECT.h / 6), (-0.5, 0.5))
        self.mini_chest = img.load(
            'mini_chest', screen, (RECT.w / 2, RECT.h * 7 / 8), (-0.5, -1))

        self.math = img.load('math', screen)
        self.mini_math = img.load('mini_math', screen, BACK_WALL.topleft)

        self.window = img.load(
            'window', screen, (RECT.w / 4, RECT.h / 2), (0, -1))
        self.mini_window = img.load(
            'mini_window', screen, (RECT.w / 16, RECT.h / 2), (0, -1))
        self.maxi_window = img.load('maxi_window', screen, (0, RECT.h / 4))

        self.zodiac = img.load('zodiac', screen)
