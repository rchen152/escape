"""Tests for escape.room."""

import pygame
from pygame.locals import *
import random
import unittest
import unittest.mock

from escape import color
from escape import room
from . import test_utils


class AtEdgeTest(unittest.TestCase):

    def test_left_edge(self):
        self.assertTrue(room.at_edge(room.RECT.midleft))

    def test_top_edge(self):
        self.assertTrue(room.at_edge(room.RECT.midtop))

    def test_right_edge(self):
        self.assertTrue(room.at_edge(room.RECT.midright))

    def test_bottom_edge(self):
        self.assertTrue(room.at_edge(room.RECT.midbottom))

    def test_center(self):
        self.assertFalse(room.at_edge(room.RECT.center))


class QuadrantTest(unittest.TestCase):

    def test_left(self):
        self.assertEqual(room.quadrant(room.RECT.midleft), room.Quadrant.LEFT)

    def test_top(self):
        self.assertEqual(room.quadrant(room.RECT.midtop), room.Quadrant.TOP)

    def test_right(self):
        self.assertEqual(room.quadrant(room.RECT.midright), room.Quadrant.RIGHT)

    def test_bottom(self):
        self.assertEqual(room.quadrant(room.RECT.midbottom),
                         room.Quadrant.BOTTOM)


class ImagesTest(test_utils.ImgTestCase):

    def test_load(self):
        with test_utils.patch('pygame.font'):
            room.Images(self.screen)


class ChestTest(test_utils.ImgTestCase):

    def setUp(self):
        super().setUp()
        with test_utils.patch('pygame.font'):
            self.chest = room.Chest(self.screen)

    def test_send_unrelated(self):
        self.assertIsNone(self.chest.send(test_utils.MockEvent(QUIT)))
        self.assertFalse(self.chest.text)

    def test_send_backspace_noop(self):
        redraw = self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_BACKSPACE))
        self.assertIs(redraw, False)
        self.assertFalse(self.chest.text)

    def test_send_backspace(self):
        self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        redraw = self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_BACKSPACE))
        self.assertIs(redraw, True)
        self.assertFalse(self.chest.text)

    def test_send_nonprintable(self):
        self.assertIsNone(
            self.chest.send(
                test_utils.MockEvent(KEYDOWN, key=K_ESCAPE, unicode='\x1b')))
        self.assertFalse(self.chest.text)

    def test_send_empty(self):
        self.assertIsNone(
            self.chest.send(
                test_utils.MockEvent(KEYDOWN, key=K_F1, unicode='')))
        self.assertFalse(self.chest.text)

    def test_send_overflow(self):
        self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.assertIs(
            self.chest.send(
                test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r')), False)
        self.assertEqual(self.chest.text, 'rrr')

    def test_send_printable(self):
        self.assertIs(
            self.chest.send(
                test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r')), True)
        self.assertEqual(self.chest.text, 'r')

    def test_opened(self):
        self.chest.text = 'AYP'
        self.assertTrue(self.chest.opened)

    def test_not_opened(self):
        self.chest.text = ''
        self.assertFalse(self.chest.opened)

    def test_send_opened(self):
        self.chest.text = 'AYP'
        self.assertIsNone(self.chest.send(
            test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r')))


class DoorTest(test_utils.ImgTestCase):

    def setUp(self):
        super().setUp()
        with test_utils.patch('pygame.font'):
            self.door = room.Door(self.screen)
        self.colors = []

    def test_collidepoint_no_revealed(self):
        self.door.revealed = False
        self.assertTrue(self.door.collidepoint(self.door._GAP.center))
        self.assertFalse(
            self.door.collidepoint((room.RECT.w / 2, room.RECT.h / 2)))
        self.assertFalse(self.door.collidepoint((0, 0)))

    def test_collidepoint_revealed(self):
        self.door.revealed = True
        self.assertTrue(self.door.collidepoint(self.door._GAP.center))
        self.assertTrue(
            self.door.collidepoint((room.RECT.w / 2, room.RECT.h / 2)))
        self.assertFalse(self.door.collidepoint((0, 0)))

    def mock_draw(self, screen, draw_color, rect, width=0):
        del screen, rect, width  # unused
        self.colors.append(draw_color)

    def _draw(self, light_switch_on, revealed):
        self.door.light_switch_on = light_switch_on
        self.door.revealed = revealed
        with unittest.mock.patch.object(pygame.draw, 'rect', self.mock_draw):
            self.door.draw()

    def test_draw_unlit_unrevealed(self):
        self._draw(False, False)
        self.assertEqual(self.colors, [color.DARK_GREY_2, color.DARK_GREY_2])

    def test_draw_unlit_revealed(self):
        self._draw(False, True)
        self.assertFalse(self.colors)

    def test_draw_lit_unrevealed(self):
        self._draw(True, False)
        self.assertEqual(self.colors, [color.DARK_GREY_1, color.DARK_GREY_1])

    def test_draw_lit_revealed(self):
        self._draw(True, True)
        self.assertFalse(self.colors)


class LightSwitchTest(test_utils.ImgTestCase):

    def setUp(self):
        super().setUp()
        self.light_switch = room.LightSwitch(self.screen)

    def test_on(self):
        self.light_switch.on = True
        self.light_switch.draw()
        expected = self.light_switch._images[1]
        self.screen.blit.assert_called_once_with(expected._img, expected._pos)

    def test_off(self):
        self.light_switch.on = False
        self.light_switch.draw()
        expected = self.light_switch._images[0]
        self.screen.blit.assert_called_once_with(expected._img, expected._pos)

    def test_collidepoint(self):
        self.assertTrue(self.light_switch.collidepoint(
            (room.RECT.w / 2, room.RECT.h / 2 - 1)))

    def test_no_collidepoint(self):
        self.assertFalse(self.light_switch.collidepoint((0, 0)))


class KeyPadTest(test_utils.ImgTestCase):

    def setUp(self):
        super().setUp()
        with test_utils.patch('pygame.font'):
            self.keypad = room.KeyPad(self.screen)

    def test_draw(self):
        self.keypad.draw()  # smoke test

    def test_opened(self):
        self.keypad.text = '9710'
        self.assertTrue(self.keypad.opened)

    def test_not_opened(self):
        self.keypad.text = ''
        self.assertFalse(self.keypad.opened)

    def test_stay_opened(self):
        self.keypad.text = '9710'
        self.assertTrue(self.keypad.opened)
        self.keypad.text = '3 + 5'
        self.assertTrue(self.keypad.opened)

    def test_text_before_opened(self):
        self.keypad.text = ''
        assert not self.keypad.opened
        self.keypad.text = '5555'
        self.assertEqual(self.keypad.text, '5555')

    def test_text_after_opened(self):
        self.keypad.text = '9710'
        assert self.keypad.opened
        self.keypad.text = '3+5'
        self.assertEqual(self.keypad.text, '3+5')

    def test_send(self):
        response = self.keypad.send(
            test_utils.MockEvent(KEYDOWN, key=K_1, unicode='1'))
        self.assertIs(response, True)
        self.assertEqual(self.keypad.text, '1')

    def test_nondigit(self):
        response = self.keypad.send(
            test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.assertIsNone(response)
        self.assertFalse(self.keypad.text)

    def test_send_unrelated(self):
        self.assertIsNone(self.keypad.send(test_utils.MockEvent(QUIT)))
        self.assertFalse(self.keypad.text)


class KeyPadTestTest(test_utils.ImgTestCase):

    _DEFAULT_RANDINTS = (5, 3, 0)
    _DEFAULT_Q = ('3', '+', '2', '5')

    def setUp(self):
        super().setUp()
        self.patches = {test_utils.patch('pygame.display'),
                        test_utils.patch('pygame.font')}
        for patch in self.patches:
            patch.start()
        self.keypad_test = room.KeyPadTest(room.KeyPad(self.screen),
                                           room.Door(self.screen))

    def tearDown(self):
        super().tearDown()
        for patch in self.patches:
            patch.stop()

    def _generate_question(self, *random_ints, add_default=False):
        if add_default:
            random_ints += self._DEFAULT_RANDINTS
        with unittest.mock.patch.object(random, 'randint') as mock_randint:
            mock_randint.side_effect = random_ints
            return self.keypad_test._generate_question()

    def _tick(self):
        self.keypad_test.send(test_utils.MockEvent(room.KeyPadTest._TICK))

    def test_add(self):
        self.assertEqual(self._generate_question(5, 3, 0), ('3', '+', '2', '5'))

    def test_mul(self):
        self.assertEqual(self._generate_question(6, 2, 1), ('2', '*', '3', '6'))

    def test_sub(self):
        self.assertEqual(self._generate_question(3, 4, 2), ('7', '-', '4', '3'))

    def test_div(self):
        self.assertEqual(self._generate_question(2, 4, 3), ('8', '/', '4', '2'))

    def test_skip_zero_mul(self):
        self.assertEqual(self._generate_question(4, 0, 1, add_default=True),
                         self._DEFAULT_Q)

    def test_skip_zero_div(self):
        self.assertEqual(self._generate_question(4, 0, 3, add_default=True),
                         self._DEFAULT_Q)

    def test_ans_zero_mul(self):
        self.assertEqual(self._generate_question(0, 5, 1), ('5', '*', '0', '0'))

    def test_ans_zero_div(self):
        self.assertEqual(self._generate_question(0, 5, 3), ('0', '/', '5', '0'))

    def test_float(self):
        self.assertEqual(self._generate_question(1, 5, 1),
                         ('5', '*', '0.2', '1'))

    def test_skip_float(self):
        self.assertEqual(self._generate_question(1, 3, 1, add_default=True),
                         self._DEFAULT_Q)

    def test_negative(self):
        self.assertEqual(self._generate_question(3, 4, 0),
                         ('4', '+', '(-1)', '3'))

    def test_start(self):
        self.keypad_test._active = False
        self.keypad_test._keypad.text_color = color.BLACK
        self.keypad_test.start()
        self.assertTrue(self.keypad_test._active)
        self.assertEqual(self.keypad_test._keypad.text_color, color.RED)

    def test_stop(self):
        self.keypad_test._active = True
        self.keypad_test._keypad.text_color = color.RED
        self.keypad_test.stop()
        self.assertFalse(self.keypad_test._active)
        self.assertEqual(self.keypad_test._keypad.text_color, color.BLACK)

    def test_send_inactive(self):
        self.keypad_test._active = False
        self.assertTrue(self.keypad_test.send(None))

    def test_send_active_ignore(self):
        self.keypad_test._active = True
        self.assertFalse(
            self.keypad_test.send(test_utils.MockEvent(MOUSEBUTTONDOWN)))

    def test_send_active_consume(self):
        self.keypad_test._active = True
        self.assertTrue(
            self.keypad_test.send(test_utils.MockEvent(room.KeyPadTest._TICK)))

    def test_question(self):
        self.keypad_test._question = None
        self.keypad_test.start()
        self._tick()
        self.assertIsNotNone(self.keypad_test._question)
        self.keypad_test.stop()
        self.assertIsNone(self.keypad_test._question)

    def test_stop_after_err(self):
        self.keypad_test.start()
        self._tick()
        # send a wrong answer
        self.keypad_test.send(test_utils.MockEvent(KEYDOWN, unicode='88'))
        self._tick()
        self.assertEqual(self.keypad_test._keypad.text, 'ERR')
        self._tick()
        self.assertFalse(self.keypad_test._active)

    def test_next_question(self):
        self.keypad_test.start()
        self._tick()
        question = self.keypad_test._question
        self.keypad_test.send(
            test_utils.MockEvent(KEYDOWN, unicode=question.value[-1]))
        self._tick()
        self.assertEqual(self.keypad_test._keypad.text, 'OK')
        self._tick()
        self.assertIsNotNone(self.keypad_test._question)
        self.assertIsNot(self.keypad_test._question, question)


class QuestionTest(unittest.TestCase):

    def test_solve_ok(self):
        question = room._Question(('3', '*', '2', '6'))
        question.solve('6')
        self.assertIs(question.state, room._QuestionState.OK)

    def test_solve_err(self):
        question = room._Question(('3', '*', '2', '6'))
        question.solve('5')
        self.assertIs(question.state, room._QuestionState.ERR)

    def test_tick(self):
        question = room._Question(None)
        question.tick()
        self.assertIs(question.state, room._QuestionState.ACTIVE)
        question.tick()
        self.assertIs(question.state, room._QuestionState.ERR)


if __name__ == '__main__':
    unittest.main()
