"""Tests for escape.state."""

from escape import state

import pygame
from pygame.locals import *

import unittest
import unittest.mock


class MockEvent:

    def __init__(self, typ, key=None):
        self.type = typ
        self.key = key


class MockGame(state.GameState):

    def __init__(self, screen):
        self.drawn = 0
        super().__init__(screen)

    def draw(self):
        self.drawn += 1


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
        self.state.handle_quit(MockEvent(KEYDOWN, K_q))
        self.assertFalse(self.state.active)

    def test_fullscreen(self):
        self.state.screen.fullscreen = False
        with unittest.mock.patch.object(
                pygame.display, 'set_mode', self.mock_set_mode):
            self.state.handle_fullscreen(MockEvent(KEYDOWN, K_f))
        self.assertTrue(self.state.screen.fullscreen)
        self.assertEqual(self.state.drawn, 2)

    def test_unfullscreen(self):
        self.state.screen.fullscreen = True
        with unittest.mock.patch.object(
                pygame.display, 'set_mode', self.mock_set_mode):
            self.state.handle_fullscreen(MockEvent(KEYDOWN, K_f))
        self.assertFalse(self.state.screen.fullscreen)
        self.assertEqual(self.state.drawn, 2)

    def test_multiple_events(self):
        self.state.screen.fullscreen = False
        with unittest.mock.patch.object(
                pygame.display, 'set_mode', self.mock_set_mode):
            self.state.handle_events([MockEvent(KEYDOWN, K_f), MockEvent(QUIT)])
        self.assertTrue(self.state.screen.fullscreen)
        self.assertEqual(self.state.drawn, 2)
        self.assertFalse(self.state.active)

    def test_run(self):
        self.state.screen.fullscreen = False
        with unittest.mock.patch.object(
                pygame.display, 'set_mode', self.mock_set_mode):
            with unittest.mock.patch.object(pygame.event, 'get') as mock_get:
                mock_get.return_value = [
                    MockEvent(KEYDOWN, K_f),
                    MockEvent(KEYDOWN, K_f),
                    MockEvent(KEYDOWN, K_q),
                ]
                self.state.run()
        self.assertFalse(self.state.screen.fullscreen)
        self.assertEqual(self.state.drawn, 3)
        self.assertFalse(self.state.active)


class TitleCardTest(unittest.TestCase):

    def test_init(self):
        with unittest.mock.patch('pygame.display', autospec=True):
            with unittest.mock.patch('pygame.image', autospec=True):
                with unittest.mock.patch('pygame.transform', autospec=True):
                    state.TitleCard(MockScreen())


class GameTest(unittest.TestCase):

    def test_init(self):
        with unittest.mock.patch('pygame.display', autospec=True):
            state.Game(MockScreen())


if __name__ == '__main__':
    unittest.main()
