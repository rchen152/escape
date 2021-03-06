"""Tests for escape.state."""

from pygame.locals import *

import unittest
import unittest.mock

from common import color  # needs to come after pygame.locals.*
from common import test_utils
from escape import room
from escape import state


def _click(x, y):
    return test_utils.MockEvent(MOUSEBUTTONDOWN, button=1, pos=(x, y))


class GameTestCase(test_utils.GameStateTestCase):

    def setUp(self):
        self.num_updates = 0
        super().setUp()
        self.mocks['pygame.display'].update = self.mock_update
        self.game = state.Game(self.screen)

    def mock_update(self):
        self.num_updates += 1


class GameTest(GameTestCase):

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
        self.game.handle_reset(test_utils.MockEvent(KEYDOWN, key=K_ESCAPE))
        self.assertEqual(self.game.view, room.View.DEFAULT)
        self.assertEqual(self.num_updates, 3)

    def test_skip_update(self):
        consumed = self.game.handle_reset(
            test_utils.MockEvent(KEYDOWN, key=K_ESCAPE))
        assert consumed  # make sure we actually reset the view
        self.assertEqual(self.game.view, room.View.DEFAULT)
        # We were already on the default view, so no need to redraw it.
        self.assertEqual(self.num_updates, 1)

    def test_non_default_view(self):
        self.game.handle_click(_click(room.RECT.w / 8, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.LEFT_WALL)
        self.game.handle_click(_click(0, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.FRONT_WALL)
        self.assertEqual(self.num_updates, 3)

    def test_left_window_view(self):
        self.game.handle_click(_click(room.RECT.w / 8, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.LEFT_WALL)
        self.game.handle_click(_click(room.RECT.w / 2, room.RECT.h / 3))
        self.assertEqual(self.game.view, room.View.LEFT_WINDOW)
        self.game.handle_click(_click(0, 0))
        self.assertEqual(self.game.view, room.View.LEFT_WALL)
        self.assertEqual(self.num_updates, 4)

    def test_front_keypad_view(self):
        self.game.handle_click(_click(0, 0))
        self.assertEqual(self.game.view, room.View.FRONT_WALL)
        self.game.handle_click(_click(3 * room.RECT.w / 5 - 2, room.RECT.h / 2))
        self.game.handle_click(_click(room.RECT.w / 2, room.RECT.h / 2))
        self.assertEqual(self.game.view, room.View.FRONT_KEYPAD)
        self.game.handle_click(_click(0, 0))
        self.assertEqual(self.game.view, room.View.FRONT_WALL)
        self.assertEqual(self.num_updates, 5)

    def test_ending(self):
        self.game.active = False
        self.game._keypad_test._question = room._Question(('1', '+', '1', '3'))
        self.game._images.keypad.text = 'OK'
        self.assertIsInstance(self.game.ending(), state.Ending)

    def test_no_ending(self):
        self.game.active = False
        self.game._keypad_test._question = None
        self.assertIsNone(self.game.ending())


class ChestTest(GameTestCase):

    def test_bad_view(self):
        self.game.view = room.View.DEFAULT
        consumed = self.game.handle_chest_combo(
            test_utils.MockEvent(KEYDOWN, key=K_r))
        self.assertFalse(consumed)
        self.assertFalse(self.game._images.chest.text)

    def test_bad_event(self):
        self.game.view = room.View.FLOOR
        consumed = self.game.handle_chest_combo(test_utils.MockEvent(QUIT))
        self.assertFalse(consumed)
        self.assertFalse(self.game._images.chest.text)

    def test_update_text(self):
        self.game.view = room.View.FLOOR
        consumed = self.game.handle_chest_combo(
            test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.assertTrue(consumed)
        self.assertEqual(self.game._images.chest.text, 'R')
        self.assertEqual(self.game._images.mini_chest.text, 'R')

    def test_max_text_length(self):
        self.game.view = room.View.FLOOR
        num_updates_1 = self.num_updates
        for _ in range(3):
            self.game.handle_chest_combo(
                test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        num_updates_2 = self.num_updates
        consumed = self.game.handle_chest_combo(
            test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.assertTrue(consumed)
        self.assertEqual(self.game._images.chest.text, 'RRR')
        self.assertEqual(num_updates_2 - num_updates_1, 3)
        self.assertEqual(self.num_updates, num_updates_2)


class LightSwitchTest(GameTestCase):

    def test_synced(self):
        self.assertTrue(self.game._images.light_switch.on)
        self.assertTrue(self.game._images.door.light_switch_on)
        self.game.view = room.View.CEILING
        blit_count = self.screen.blit.call_count
        self.game.draw()
        self.assertEqual(self.screen.blit.call_count, blit_count)

    def test_zodiac(self):
        self.game._images.light_switch.on = False
        self.game.view = room.View.CEILING
        blit_count = self.screen.blit.call_count
        self.game.draw()
        self.assertEqual(self.screen.blit.call_count, blit_count + 1)

    def test_click(self):
        self.game.view = room.View.RIGHT_WALL
        self.game.handle_click(test_utils.MockEvent(
            MOUSEBUTTONDOWN, button=1,
            pos=(room.RECT.w / 2, room.RECT.h / 2 - 1)))
        self.assertFalse(self.game._images.light_switch.on)
        self.assertFalse(self.game._images.door.light_switch_on)


class KeyPadTest(GameTestCase):

    def test_update_text(self):
        self.game.view = room.View.FRONT_KEYPAD
        consumed = self.game.handle_keypad_input(
            test_utils.MockEvent(KEYDOWN, key=K_1, unicode='1'))
        self.assertTrue(consumed)
        self.assertEqual(self.game._images.keypad.text, '1')
        self.assertEqual(self.game._images.door.text, '1')

    def test_test(self):
        self.game.view = room.View.FRONT_KEYPAD
        # test is inactive
        consumed = self.game.handle_keypad_test(
            test_utils.MockEvent(MOUSEBUTTONDOWN))
        self.assertFalse(consumed)
        self.assertFalse(self.game._images.keypad.opened)
        self.assertFalse(self.game._keypad_test._active)
        # test is active after keypad is opened
        self.game._images.door.text = self.game._images.keypad.text = '9710'
        consumed = self.game.handle_keypad_test(
            test_utils.MockEvent(MOUSEBUTTONDOWN))
        self.assertTrue(consumed)
        self.assertTrue(self.game._images.keypad.opened)
        self.assertTrue(self.game._keypad_test._active)
        # clicking away stops the test and resets the keypad
        self.game.handle_click(test_utils.MockEvent(MOUSEBUTTONDOWN, button=1,
                                                    pos=(0, 0)))
        self.assertFalse(self.game._images.keypad.opened)
        self.assertFalse(self.game._keypad_test._active)
        self.assertFalse(self.game._images.keypad.text)
        self.assertFalse(self.game._images.door.text)

    def test_win(self):
        self.game.active = True
        self.game._images.keypad.text = '9710'
        self.game._keypad_test.start()
        self.game._keypad_test._question = room._Question(('1', '+', '1', '3'))
        self.game.handle_keypad_test(test_utils.MockEvent(KEYDOWN, unicode='3'))
        self.game.handle_keypad_test(
            test_utils.MockEvent(room.KeyPadTest._TICK))
        self.assertFalse(self.game.active)


class EndingTest(test_utils.GameStateTestCase):

    def setUp(self):
        super().setUp()
        self.keypad = unittest.mock.MagicMock()
        self.ending = state.Ending(self.screen, color.GREY, self.keypad)

    def test_keypad(self):
        self.ending._frame = state._EndingFrame.KEYPAD
        self.ending.draw()
        self.assertEqual(self.keypad.draw.call_count, 2)

    def test_keypad_blue(self):
        self.ending._frame = state._EndingFrame.KEYPAD_BLUE
        self.ending.draw()
        self.assertEqual(self.keypad.draw.call_count, 2)

    def test_door(self):
        self.ending._frame = state._EndingFrame.DOOR
        self.ending.draw()
        self.assertEqual(self.keypad.draw.call_count, 1)
        self.screen.fill.assert_called_with(color.GREY)

    def _test_text_frame(self, frame):
        self.ending._frame = frame
        self.ending.draw()
        self.assertEqual(self.keypad.draw.call_count, 1)
        self.screen.fill.assert_called_with(color.BLUE)

    def test_congrats(self):
        self._test_text_frame(state._EndingFrame.CONGRATS)

    def test_detail(self):
        self._test_text_frame(state._EndingFrame.DETAIL)

    def test_warning(self):
        self._test_text_frame(state._EndingFrame.WARNING)

    def test_fin(self):
        self.ending.active = True
        self.ending._frame = state._EndingFrame.FIN - 1
        self.ending.handle_tick(test_utils.MockEvent(state.Ending._TICK))
        self.assertFalse(self.ending.active)


if __name__ == '__main__':
    unittest.main()
