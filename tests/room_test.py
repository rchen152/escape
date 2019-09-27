"""Tests for escape.room."""

from escape import room
import unittest


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


if __name__ == '__main__':
    unittest.main()
