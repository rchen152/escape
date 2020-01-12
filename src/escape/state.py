"""Game state."""

from common import state
import enum
import pygame
from pygame.locals import *
from common import color  # needs to come after pygame.locals.*
from . import room


class Game(state.GameState):

    def __init__(self, screen):
        self.view = room.View.DEFAULT
        self._images = room.Images(screen)
        self._keypad_test = room.KeyPadTest(
            self._images.keypad, self._images.door)
        self._wall_color = color.GREY
        super().__init__(screen)

    def _draw_default(self):
        pygame.draw.rect(self.screen, color.BLACK, room.BACK_WALL, 5)
        for corner in ('topleft', 'bottomleft', 'bottomright', 'topright'):
            pygame.draw.line(
                self.screen, color.BLACK, getattr(room.RECT, corner),
                getattr(room.BACK_WALL, corner), 5)
        if not self._images.light_switch.on:
            self._images.mini_zodiac.draw()
        self._images.mini_window.draw()
        self._images.mini_math.draw()
        self._images.mini_chest.draw()
        self._images.mini_light_switch.draw()

    def _draw_back_wall(self):
        self._images.math.draw()

    def _draw_front_wall(self):
        self._images.door.draw()

    def _draw_front_keypad(self):
        self.screen.fill(color.DARK_GREY_2)
        self._images.keypad.draw()

    def _draw_floor(self):
        self._images.chest.draw()

    def _draw_ceiling(self):
        if not self._images.light_switch.on:
            self._images.zodiac.draw()

    def _draw_left_wall(self):
        self._images.window.draw()

    def _draw_left_window(self):
        self._images.maxi_window.draw()

    def _draw_right_wall(self):
        self._images.light_switch.draw()

    def draw(self):
        """Draw the current view.

        First fills in the wall color, then calls _draw_<lowercase view name>.
        """
        self.screen.fill(self._wall_color)
        if self._images.keypad.opened and self.view != room.View.FRONT_KEYPAD:
            # Navigating away from the keypad after opening resets it.
            self._keypad_test.stop()
        view = self.view.name.lower()
        getattr(self, f'_draw_{view}')()
        pygame.display.update()

    def _handle_default_click(self, pos):
        if room.at_edge(pos):
            # In the default view, the edges of the screen border the (hidden)
            # front wall.
            self.view = room.View.FRONT_WALL
        elif self._images.mini_chest.collidepoint(pos):
            # Clicking in the intersection of the chest on the floor and the
            # back wall should take us to the floor, not the wall.
            self.view = room.View.FLOOR
        elif room.BACK_WALL.collidepoint(pos):
            # The back wall is a rectangle, so use built-in collision detection.
            self.view = room.View.BACK_WALL
        else:
            # Since we've already checked the front and back walls, the quadrant
            # corresponds to one of the other four walls.
            self.view = room.View(room.quadrant(pos).value)
        return True

    def _handle_generic_click(self, pos):
        if not room.at_edge(pos):
            return False
        quadrant = room.quadrant(pos)
        self.view = room.View(
            room.ROTATIONS[self.view].get(quadrant, quadrant.value))
        return True

    def _handle_left_wall_click(self, pos):
        if not self._images.window.collidepoint(pos):
            return False
        self.view = room.View.LEFT_WINDOW
        return True

    def _handle_front_wall_click(self, pos):
        if not self._images.door.collidepoint(pos):
            return False
        if self._images.door.revealed:
            self.view = room.View.FRONT_KEYPAD
        else:
            self._images.door.revealed = True
        return True

    def _toggle_light_switch(self):
        self._images.light_switch.on = not self._images.light_switch.on
        self._images.mini_light_switch.on = self._images.light_switch.on
        if self._images.light_switch.on:
            self._wall_color = color.GREY
        else:
            self._wall_color = color.DARK_GREY_2
        self._images.door.light_switch_on = self._images.light_switch.on

    def _handle_right_wall_click(self, pos):
        if not self._images.light_switch.collidepoint(pos):
            return False
        self._toggle_light_switch()
        return True

    def handle_click(self, event):
        """Handle left mouse clicks.

        If the event is a left click, tries to call
        _handle_{lowercase view name}. If it does not exist or returns False,
        falls back to _handle_generic_click.

        Args:
          event: An event.
        """
        if event.type != MOUSEBUTTONDOWN or event.button != 1:
            return False
        view = self.view.name.lower()
        handle_view_click = getattr(self, f'_handle_{view}_click', None)
        if handle_view_click:
            consumed = handle_view_click(event.pos)
        else:
            consumed = False
        if not consumed:
            consumed = self._handle_generic_click(event.pos)
        if consumed:
            self.draw()
        return consumed

    def handle_reset(self, event):
        if not state.keypressed(event, K_ESCAPE):
            return False
        if self.view is not room.View.DEFAULT:
            self.view = room.View.DEFAULT
            self.draw()
        return True

    def handle_chest_combo(self, event):
        if self.view is not room.View.FLOOR:
            return False
        response = self._images.chest.send(event)
        if response is None:
            return False
        if response:
            if self._images.chest.opened:
                self.draw()
            else:
                # Optimization: only redraw the chest area.
                self._images.chest.draw()
                pygame.display.update()
            self._images.mini_chest.text = self._images.chest.text
        return True

    def handle_keypad_input(self, event):
        if self.view is not room.View.FRONT_KEYPAD:
            return False
        response = self._images.keypad.send(event)
        if response is None:
            return False
        if response:
            self._images.keypad.draw()
            pygame.display.update()
            self._images.door.text = self._images.keypad.text
        return True

    def handle_keypad_test(self, event):
        if not self._images.keypad.opened:
            return False
        consumed = self._keypad_test.send(event)
        if consumed:
            self._images.keypad.draw()
            pygame.display.update()
        if self._keypad_test.completed:
            self.active = False
        return consumed

    def ending(self):
        assert not self.active
        if self._keypad_test.completed:
            return Ending(self.screen, self._wall_color, self._images.keypad)
        return None


class _EndingFrame(enum.IntEnum):
    """Frames of the ending sequence.

    Each frame is displayed for
    (next_frame - current_frame) * Ending._WAIT_INTERVAL_MS milliseconds.
    """
    KEYPAD = 0
    KEYPAD_BLUE = 1
    DOOR = 2
    CONGRATS = 4
    DETAIL = 5
    WARNING = 7
    FIN = 9


class Ending(state.GameState):

    _TICK = pygame.USEREVENT
    _WAIT_INTERVAL_MS = 1250

    _OPEN_DOOR = [room.DOOR_RECT.topleft,
                  (room.DOOR_RECT.left + 20, room.DOOR_RECT.top + 20),
                  (room.DOOR_RECT.left + 20, room.DOOR_RECT.bottom - 10),
                  room.DOOR_RECT.bottomleft]

    def __init__(self, screen, wall_color, keypad):
        self._wall_color = wall_color
        self._keypad = keypad
        self._frame = 0
        self._font = pygame.font.SysFont('couriernew', 100, bold=True)
        super().__init__(screen)
        pygame.time.set_timer(self._TICK, self._WAIT_INTERVAL_MS)

    def _render_text(self, text, raw_pos):
        surface = self._font.render(text, 0, color.BLACK)
        size = surface.get_size()
        pos = tuple(raw_pos[i] - size[i] / 2 for i in range(2))
        self.screen.blit(surface, pos)

    def draw(self):
        if self._frame in (_EndingFrame.KEYPAD, _EndingFrame.KEYPAD_BLUE):
            self.screen.fill(color.DARK_GREY_2)
            self._keypad.draw()
        elif self._frame < _EndingFrame.CONGRATS:
            self.screen.fill(self._wall_color)
            pygame.draw.rect(self.screen, color.BLUE, room.DOOR_RECT)
            pygame.draw.polygon(self.screen, color.DARK_GREY_2, self._OPEN_DOOR)
            pygame.draw.rect(self.screen, color.BLACK, room.DOOR_RECT, 5)
        else:
            self.screen.fill(color.BLUE)
            self._render_text('Congratulations',
                              (room.RECT.w / 2, room.RECT.h / 4))
            if self._frame >= _EndingFrame.DETAIL:
                self._render_text('you escaped',
                                  (room.RECT.w / 2, room.RECT.h / 2))
            if self._frame >= _EndingFrame.WARNING:
                self._render_text('for now...',
                                  (room.RECT.w / 2, 3 * room.RECT.h / 4))
        pygame.display.update()

    def handle_tick(self, event):
        if event.type != self._TICK:
            return False
        self._frame += 1
        if self._frame == _EndingFrame.FIN:
            self.active = False
            return True
        elif self._frame == _EndingFrame.KEYPAD_BLUE:
            self._keypad.text_color = color.BLUE
        self.draw()
        return True

    def cleanup(self):
        pygame.time.set_timer(self._TICK, 0)
