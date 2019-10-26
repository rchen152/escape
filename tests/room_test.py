"""Tests for escape.room."""

import pygame
from pygame.locals import *
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


class FrontDoorTest(test_utils.ImgTestCase):

    def setUp(self):
        super().setUp()
        with test_utils.patch('pygame.font'):
            self.front_door = room.FrontDoor(self.screen)
        self.colors = []

    def test_collidepoint_no_revealed(self):
        self.front_door.revealed = False
        self.assertTrue(
            self.front_door.collidepoint(self.front_door._GAP.center))
        self.assertFalse(
            self.front_door.collidepoint((room.RECT.w / 2, room.RECT.h / 2)))
        self.assertFalse(self.front_door.collidepoint((0, 0)))

    def test_collidepoint_revealed(self):
        self.front_door.revealed = True
        self.assertTrue(
            self.front_door.collidepoint(self.front_door._GAP.center))
        self.assertTrue(
            self.front_door.collidepoint((room.RECT.w / 2, room.RECT.h / 2)))
        self.assertFalse(self.front_door.collidepoint((0, 0)))

    def mock_draw(self, screen, draw_color, rect, width=0):
        del screen, rect, width  # unused
        self.colors.append(draw_color)

    def _draw(self, light_switch_on, revealed):
        self.front_door.light_switch_on = light_switch_on
        self.front_door.revealed = revealed
        with unittest.mock.patch.object(pygame.draw, 'rect', self.mock_draw):
            self.front_door.draw()

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


if __name__ == '__main__':
    unittest.main()
