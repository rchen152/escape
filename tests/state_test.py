"""Tests for escape.state."""

from escape import state

from pygame.locals import *

import unittest
import unittest.mock


class MockEvent:

    def __init__(self, typ, key=None):
        self.type = typ
        self.key = key


class GameStateTest(unittest.TestCase):

    def setUp(self):
        self.state = state.GameState()

    def test_quit_x(self):
        self.assertTrue(self.state.active)
        self.state.handle_quit(MockEvent(QUIT))
        self.assertFalse(self.state.active)

    def test_quit_q(self):
        self.assertTrue(self.state.active)
        self.state.handle_quit(MockEvent(KEYDOWN, K_q))
        self.assertFalse(self.state.active)

    @unittest.mock.patch('pygame.display', autospec=True)
    def test_fullscreen(self, display_mock):
        display_mock.get_surface.return_value.get_flags.return_value = 0
        self.state.handle_fullscreen(MockEvent(KEYDOWN, K_f))
        display_mock.set_mode.assert_called_once_with(state.WINSIZE, FULLSCREEN)

    @unittest.mock.patch('pygame.display', autospec=True)
    def test_unfullscreen(self, display_mock):
        display_mock.get_surface.return_value.get_flags.return_value = (
            FULLSCREEN)
        self.state.handle_fullscreen(MockEvent(KEYDOWN, K_f))
        display_mock.set_mode.assert_called_once_with(state.WINSIZE)

    @unittest.mock.patch('pygame.display', autospec=True)
    def test_multiple_events(self, display_mock):
        display_mock.get_surface.return_value.get_flags.return_value = 0
        self.state.handle_events([MockEvent(KEYDOWN, K_f), MockEvent(QUIT)])
        display_mock.set_mode.assert_called_once_with(state.WINSIZE, FULLSCREEN)
        self.assertFalse(self.state.active)


if __name__ == '__main__':
    unittest.main()
