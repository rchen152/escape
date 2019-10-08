"""Game state."""

import abc
import pygame
from pygame.locals import *
from . import color
from . import img
from . import room


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
        if event.type == QUIT or _keypressed(event, K_ESCAPE):
            self.active = False
            return True
        return False

    def handle_fullscreen(self, event):
        if not _keypressed(event, K_F11):
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
        self._title_card_img = img.load('title_card', screen)
        super().__init__(screen)
        pygame.time.set_timer(self._TIMED_QUIT, self._DISPLAY_TIME_MS)

    def draw(self):
        self.screen.fill(color.BLUE)
        self._title_card_img.draw()
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
        self._images = room.Images(screen)
        self._wall_color = color.GREY
        super().__init__(screen)

    def _draw_default(self):
        pygame.draw.rect(self.screen, color.BLACK, room.BACK_WALL, 5)
        for corner in ('topleft', 'bottomleft', 'bottomright', 'topright'):
            pygame.draw.line(
                self.screen, color.BLACK, getattr(room.RECT, corner),
                getattr(room.BACK_WALL, corner), 5)
        self._images.mini_window.draw()
        self._images.mini_math.draw()
        self._images.mini_chest.draw()
        self._images.mini_light_switch.draw()

    def _draw_back_wall(self):
        self._images.math.draw()

    def _draw_front_wall(self):
        self._images.front_door.draw()

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
        if not self._images.front_door.collidepoint(pos):
            return False
        self._images.front_door.revealed = True
        return True

    def _toggle_light_switch(self):
        self._images.light_switch.on = not self._images.light_switch.on
        self._images.mini_light_switch.on = self._images.light_switch.on
        if self._images.light_switch.on:
            self._wall_color = color.GREY
        else:
            self._wall_color = color.DARK_GREY_2
        self._images.front_door.light_switch_on = self._images.light_switch.on

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
        if not _keypressed(event, K_F5):
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
            self._images.chest.draw()
            pygame.display.update()
            self._images.mini_chest.text = self._images.chest.text
        return True
