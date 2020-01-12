"""Game room."""

import abc
from common import state as common_state
import enum
import pygame
from pygame.locals import *
import random
import string
from typing import Dict, List, NamedTuple, Tuple
from . import color
from . import img


RECT = common_state.RECT
BACK_WALL = pygame.Rect(RECT.w / 4, RECT.h / 4, RECT.w / 2, RECT.h / 2)
DOOR_RECT = pygame.Rect(2 * RECT.w / 5, RECT.h / 4, RECT.w / 5, 3 * RECT.h / 4)


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
    return x <= 10 or y <= 10 or RECT.w - x <= 10 or RECT.h - y <= 10


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


def _font(size):
    return pygame.font.SysFont('couriernew', size, bold=True)


class _TextMixin(abc.ABC):

    _MAX_TEXT_LENGTH: int
    text: str

    @abc.abstractmethod
    def accept_event(self, event):
        raise NotImplementedError()

    @abc.abstractmethod
    def to_char(self, event):
        raise NotImplementedError()

    def send(self, event):
        """Sends an event that may be consumed as text input.

        Args:
          event: An event.

        Returns:
          None if the event should not be consumed.
          False if the event is consumed but a redraw is not required.
          True if the event is consumed and a redraw is required.
        """
        if not self.accept_event(event):
            return None
        if event.key == K_BACKSPACE:
            # Backspace is consumed as deletion of the rightmost character;
            # whether it requires a redraw depends on whether there exists a
            # character to delete.
            redraw = bool(self.text)
            self.text = self.text[:-1]
            return redraw
        c = self.to_char(event)
        if not c:
            return None
        if len(self.text) >= self._MAX_TEXT_LENGTH:
            return False
        self.text += c
        return True


class _ChestBase(img.Factory):

    _CHARPOS: List[Tuple[int, int]]
    _FONT_SIZE: int

    def __init__(self, names, screen, position, shift):
        super().__init__(screen)
        self._font = _font(self._FONT_SIZE)
        self._images = [
            img.load(name, screen, position, shift) for name in names]
        self.text = ''

    @property
    def opened(self):
        return self.text == 'AYP'

    def draw(self):
        self._images[self.opened].draw()
        if not self.opened:
            for c, pos in zip(self.text, self._CHARPOS):
                self._screen.blit(self._font.render(c, 0, color.BLACK), pos)

    def collidepoint(self, pos):
        return self._images[self.opened].collidepoint(pos)


class Chest(_TextMixin, _ChestBase):

    _CHARPOS = [(496, 278), (509, 278), (521, 278)]
    _FONT_SIZE = 15
    _MAX_TEXT_LENGTH = 3

    def __init__(self, screen):
        super().__init__(('chest', 'chest_opened'), screen,
                         (RECT.w / 2, 2 * RECT.h / 3), (-0.5, -1))

    def accept_event(self, event):
        return event.type == KEYDOWN and not self.opened

    def to_char(self, event):
        if not event.unicode or event.unicode not in string.printable:
            # Aside from backspace, only printable characters are consumed.
            return None
        return event.unicode.upper()


class MiniChest(_ChestBase):

    _CHARPOS = [(501, 430), (510, 430), (519, 430)]
    _FONT_SIZE = 10

    def __init__(self, screen):
        super().__init__(('mini_chest', 'mini_chest_opened'), screen,
                         (RECT.w / 2, RECT.h * 7 / 8), (-0.5, -1))


class _DigitsBase(img.Factory):

    _DIGITS: Dict[str, Tuple[int, int]]
    _FONT_SIZE: int

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # pytype: disable=wrong-arg-count
        self._font = _font(self._FONT_SIZE)
        self._digits = tuple(
            self._font.render(d, 0, color.BLACK) for d in self._DIGITS)

    def draw(self):
        super().draw()
        for i, pos in enumerate(self._DIGITS.values()):
            self._screen.blit(self._digits[i], pos)


class Door(_DigitsBase):

    _GAP = pygame.Rect(
        DOOR_RECT.right - 5, DOOR_RECT.top - 2, 10, DOOR_RECT.h + 2)

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
    _FONT_SIZE = 10

    def __init__(self, screen):
        super().__init__(screen)
        self._door = img.load('door', screen, (RECT.w / 2, RECT.h), (-0.5, -1))
        self.revealed = False
        self.light_switch_on = True
        self.text = ''

    def draw(self):
        if self.revealed:
            self._door.draw()
            super().draw()
            self._screen.blit(
                self._font.render(self.text, 0, color.BLACK), (570, 325))
            return
        if self.light_switch_on:
            gap_color = color.DARK_GREY_1
        else:
            gap_color = color.DARK_GREY_2
        pygame.draw.rect(self._screen, gap_color, DOOR_RECT, 5)
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


class _KeyPadText(NamedTuple):
    value: str
    pos: Tuple[int, int]
    font: pygame.font.Font
    color: Tuple[int, int, int]


class KeyPad(_DigitsBase, _TextMixin, img.PngFactory):

    _DIGITS = {
        '1': (417, 183),
        '2': (487, 183),
        '3': (557, 183),
        '4': (417, 270),
        '5': (487, 270),
        '6': (557, 270),
        '7': (417, 355),
        '8': (487, 355),
        '9': (557, 355),
        '0': (487, 442),
    }
    _FONT_SIZE = 85
    _MAX_TEXT_LENGTH = 4
    _TEXT_POS = (410, 50)

    def __init__(self, screen):
        super().__init__('keypad', screen, (RECT.w / 2, 0), (-0.5, 0))
        self.set_initial_text()

    def set_initial_text(self):
        # the text that renders on the keypad
        self._text = _KeyPadText(value='', pos=self._TEXT_POS, font=self._font,
                                 color=color.BLACK)
        # the current input for opening the keypad, differs from self.text when
        # the keypad is already open
        self._opening_input = ''

    def _resized_text(self, value):
        assert self.opened
        max_size = self._font.size(self._opening_input)
        font_size = self._FONT_SIZE
        font = self._font
        size = font.size(value)
        while any(dim > max_dim for dim, max_dim in zip(size, max_size)):
            font_size -= 10
            font = _font(font_size)
            size = font.size(value)
        pos = tuple(self._TEXT_POS[i] + (max_size[i] - size[i]) / 2
                    for i in range(2))
        return self._text._replace(value=value, pos=pos, font=font)

    @property
    def text(self):
        return self._text.value

    @text.setter
    def text(self, value):
        if self.opened:
            self._text = self._resized_text(value)
        else:
            self._text = self._text._replace(value=value)
            self._opening_input = value

    @property
    def text_color(self):
        return self._text.color

    @text_color.setter
    def text_color(self, color):
        self._text = self._text._replace(color=color)

    @property
    def opened(self):
        return self._opening_input == '9710'

    def accept_event(self, event):
        return event.type == KEYDOWN and not self.opened

    def to_char(self, event):
        return event.unicode if event.unicode.isdigit() else None

    def draw(self):
        super().draw()
        text = self._text.font.render(self.text, 0, self._text.color)
        self._screen.blit(text, self._text.pos)


class Images:

    def __init__(self, screen):
        self.chest = img.load(screen, factory=Chest)
        self.mini_chest = img.load(screen, factory=MiniChest)

        self.door = img.load(screen, factory=Door)

        self.keypad = img.load(screen, factory=KeyPad)

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


class _QuestionState(enum.Enum):
    ACTIVE = ''
    OK = 'OK'
    ERR = 'ERR'


class _Question:

    def __init__(self, value):
        self.value = value
        self.state = _QuestionState.ACTIVE
        self._num_ticks = 0

    def solve(self, answer):
        if answer == self.value[-1]:
            self.state = _QuestionState.OK
        else:
            self.state = _QuestionState.ERR

    def tick(self):
        self._num_ticks += 1
        if self._num_ticks > 1:
            self.state = _QuestionState.ERR


class KeyPadTest:

    _TICK = pygame.USEREVENT
    _FREQ_MS = 500

    _OPERATOR_REPR = {int.__add__: '+', int.__mul__: '*', int.__sub__: '-',
                      int.__truediv__: '/'}
    _OPERATORS = tuple(_OPERATOR_REPR)

    _SPECIAL_QUESTION = ('1', '+', '1', '3')

    def __init__(self, keypad, door):
        self._keypad = keypad
        self._door = door
        self._init_state()

    def _init_state(self):
        self._active = False
        self._question = None
        self._special_question_position = random.randint(9, 14)
        self._num_questions_asked = 0

    def _generate_question(self):
        if self._num_questions_asked == self._special_question_position:
            return self._SPECIAL_QUESTION
        answer = random.randint(0, 9)
        operand1 = random.randint(0, 9)
        operator_idx = random.randint(0, 3)
        operator = self._OPERATORS[operator_idx]
        if not operand1 and operator_idx % 2:  # avoid 0 * x and x / 0
            return self._generate_question()
        elif answer == 2 and operand1 == 1 and not operator_idx:  # avoid 1 + 1
            return self._generate_question()
        # Use the inverse operator to compute the other operand.
        operand2 = self._OPERATORS[(operator_idx + 2) % 4](answer, operand1)
        if round(operand2, 1) != operand2:
            # Reject questions where the second operand has more than one digit
            # after the decimal point.
            return self._generate_question()
        if operator_idx > 1:  # for - and /, we need to flip the operands
            operand1, operand2 = operand2, operand1

        def to_str(n):
            # int / int produces a float - convert floats to ints when possible.
            s = str(int(n) if round(n, 0) == n else n)
            # Parenthesize negative numbers for readability.
            return f'({s})' if n < 0 else s

        return (to_str(operand1), self._OPERATOR_REPR[operator],
                to_str(operand2), str(answer))

    def _next_question(self):
        self._question = _Question(self._generate_question())
        self._keypad.text = ''.join(self._question.value[:3])
        self._num_questions_asked += 1

    @property
    def completed(self):
        return (self._question and
                self._question.value == self._SPECIAL_QUESTION and
                self._keypad.text == _QuestionState.OK.value)

    def start(self):
        assert not self._active
        self._active = True
        self._keypad.text_color = color.RED
        pygame.time.set_timer(self._TICK, self._FREQ_MS)

    def stop(self):
        assert self._active
        self._init_state()
        self._keypad.set_initial_text()
        self._door.text = self._keypad.text
        pygame.time.set_timer(self._TICK, 0)

    def send(self, event):
        if not self._active:
            self.start()
            return True
        elif event.type == self._TICK:
            if self._keypad.text == _QuestionState.ERR.value:
                self.stop()
                return True
            elif self.completed:
                return True
            elif (not self._question or
                  self._keypad.text == _QuestionState.OK.value):
                self._next_question()
            elif self._question.state is not _QuestionState.ACTIVE:
                self._keypad.text = self._question.state.value
            else:
                self._question.tick()
            self._flip_text_color()
            return True
        elif event.type == KEYDOWN and event.unicode.isdigit():
            if self._question:
                self._question.solve(event.unicode)
            return True
        return False

    def _flip_text_color(self):
        if self._keypad.text_color == color.BLACK:
            self._keypad.text_color = color.RED
        else:
            self._keypad.text_color = color.BLACK
