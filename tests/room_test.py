"""Tests for escape.room."""

from escape import room
from pygame.locals import *
import unittest
import unittest.mock
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


class ChestImageTest(test_utils.ImgTestCase):

    def setUp(self):
        super().setUp()
        with test_utils.patch('pygame.font'):
            self.chest = room.ChestImage(self.screen)

    def test_send_unrelated(self):
        self.assertIsNone(self.chest.send(test_utils.MockEvent(QUIT)))

    def test_send_backspace_noop(self):
        redraw = self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_BACKSPACE))
        self.assertIs(redraw, False)

    def test_send_backspace(self):
        self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        redraw = self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_BACKSPACE))
        self.assertIs(redraw, True)

    def test_send_nonprintable(self):
        self.assertIsNone(
            self.chest.send(
                test_utils.MockEvent(KEYDOWN, key=K_ESCAPE, unicode='\x1b')))

    def test_send_empty(self):
        self.assertIsNone(
            self.chest.send(
                test_utils.MockEvent(KEYDOWN, key=K_F1, unicode='')))

    def test_send_overflow(self):
        self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.chest.send(test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r'))
        self.assertIs(
            self.chest.send(
                test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r')), False)

    def test_send_printable(self):
        self.assertIs(
            self.chest.send(
                test_utils.MockEvent(KEYDOWN, key=K_r, unicode='r')), True)


if __name__ == '__main__':
    unittest.main()
