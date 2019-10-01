"""Tests for escape.state."""

from escape import room
from escape import state

import pygame
from pygame.locals import *

import unittest
import unittest.mock

from . import test_utils


class MockEvent:

    def __init__(self, typ, **kwargs):
        self.type = typ
        for k, v in kwargs.items():
            setattr(self, k, v)


def _click(x, y):
    return MockEvent(MOUSEBUTTONUP, button=1, pos=(x, y))


class MockGame(state.GameState):

    def __init__(self, screen):
        self.drawn = 0
        self.clean = False
        super().__init__(screen)

    def draw(self):
        self.drawn += 1

    def cleanup(self):
        self.clean = True


class MockScreen:

    def __init__(self):
        self.fullscreen = False

    def get_flags(self):
        return FULLSCREEN if self.fullscreen else 0

    def __getattr__(self, name):
        return unittest.mock.MagicMock()


class GameStateTest(unittest.TestCase):

    def setUp(self):
        self.state = MockGame(MockScreen())

    def mock_set_mode(self, size, fullscreen=False):
        del size  # unused
        self.state.screen.fullscreen = fullscreen

    def test_abstract(self):
        with self.assertRaises(TypeError):
            state.GameState(MockScreen())  # pytype: disable=not-instantiable

    def test_basic(self):
        self.assertTrue(self.state.active)
        self.assertEqual(self.state.drawn, 1)

    def test_quit_x(self):
        self.assertTrue(self.state.active)
        self.state.handle_quit(MockEvent(QUIT))
        self.assertFalse(self.state.active)

    def test_quit_q(self):
        self.assertTrue(self.state.active)
        self.state.handle_quit(MockEvent(KEYDOWN, key=K_q))
        self.assertFalse(self.state.active)

    def test_fullscreen(self):
        self.state.screen.fullscreen = False
        with unittest.mock.patch.object(
                pygame.display, 'set_mode', self.mock_set_mode):
            self.state.handle_fullscreen(MockEvent(KEYDOWN, key=K_f))
        self.assertTrue(self.state.screen.fullscreen)
        self.assertEqual(self.state.drawn, 2)

    def test_unfullscreen(self):
        self.state.screen.fullscreen = True
        with unittest.mock.patch.object(
                pygame.display, 'set_mode', self.mock_set_mode):
            self.state.handle_fullscreen(MockEvent(KEYDOWN, key=K_f))
        self.assertFalse(self.state.screen.fullscreen)
        self.assertEqual(self.state.drawn, 2)

    def test_run(self):
        self.state.screen.fullscreen = False
        with unittest.mock.patch.object(
                pygame.display, 'set_mode', self.mock_set_mode):
            with unittest.mock.patch.object(pygame.event, 'get') as mock_get:
                mock_get.return_value = [
                    MockEvent(KEYDOWN, key=K_f),
                    MockEvent(KEYDOWN, key=K_f),
                    MockEvent(KEYDOWN, key=K_f),
                    MockEvent(KEYDOWN, key=K_q),
                ]
                self.state.run()
        self.assertTrue(self.state.screen.fullscreen)
        self.assertEqual(self.state.drawn, 4)
        self.assertFalse(self.state.active)

    def test_cleanup(self):
        self.assertFalse(self.state.clean)
        with unittest.mock.patch.object(pygame.event, 'get') as mock_get:
            mock_get.return_value = [MockEvent(QUIT)]
            self.state.run()
        self.assertTrue(self.state.clean)


class TitleCardTest(unittest.TestCase):

    def test_init(self):
        with test_utils.patch('pygame.display', autospec=True):
            with test_utils.patch('pygame.image', autospec=True):
                with test_utils.patch('pygame.transform', autospec=True):
                    state.TitleCard(MockScreen())


class GameTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.num_updates = 0
        self.patches = {
            mod: test_utils.patch(mod)
            for mod in (
                'pygame.display',
                'pygame.draw',
                'pygame.font',
                'pygame.image',
            )}
        self.mocks = {mod: patch.start() for mod, patch in self.patches.items()}
        self.mocks['pygame.display'].update = self.mock_update
        self.game = state.Game(MockScreen())

    def tearDown(self):
        super().tearDown()
        for patch in self.patches.values():
            patch.stop()

    def mock_update(self):
        self.num_updates += 1

    def test_default_view(self):
        self.assertEqual(self.game.view, room.View.DEFAULT)
        self.assertEqual(self.num_updates, 1)

    def test_back_wall_view(self):
        self.game.handle_click(_click(room.RECT.w / 2, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.BACK_WALL)
        self.assertEqual(self.num_updates, 2)

    def test_left_wall_view(self):
        self.game.handle_click(_click(room.RECT.w / 8, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.LEFT_WALL)
        self.assertEqual(self.num_updates, 2)

    def test_ceiling_view(self):
        self.game.handle_click(_click(room.RECT.w / 2, room.RECT.h / 8))
        self.assertEqual(self.game.view, room.View.CEILING)
        self.assertEqual(self.num_updates, 2)

    def test_right_wall_view(self):
        self.game.handle_click(_click(room.RECT.w * 7 / 8, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.RIGHT_WALL)
        self.assertEqual(self.num_updates, 2)

    def test_floor_view(self):
        self.game.handle_click(_click(room.RECT.w / 2, room.RECT.h * 7 / 8))
        self.assertEqual(self.game.view, room.View.FLOOR)
        self.assertEqual(self.num_updates, 2)

    def test_front_wall_view(self):
        self.game.handle_click(_click(0, 0))
        self.assertEqual(self.game.view, room.View.FRONT_WALL)
        self.assertEqual(self.num_updates, 2)

    def test_reset_view(self):
        self.game.handle_click(_click(room.RECT.w / 8, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.LEFT_WALL)
        self.game.handle_reset(MockEvent(KEYDOWN, key=K_r))
        self.assertEqual(self.game.view, room.View.DEFAULT)
        self.assertEqual(self.num_updates, 3)

    def test_skip_update(self):
        consumed = self.game.handle_reset(MockEvent(KEYDOWN, key=K_r))
        assert consumed  # make sure we actually reset the view
        self.assertEqual(self.game.view, room.View.DEFAULT)
        # We were already on the default view, so no need to redraw it.
        self.assertEqual(self.num_updates, 1)

    def test_non_default_view(self):
        self.game.handle_click(_click(room.RECT.w / 8, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.LEFT_WALL)
        self.game.handle_click(_click(0, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.FRONT_WALL)


if __name__ == '__main__':
    unittest.main()
