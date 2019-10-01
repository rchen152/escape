"""Tests for escape.img."""

from escape import img
import unittest
import unittest.mock
from . import test_utils


class LoadTest(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.patch = test_utils.patch('pygame.image')
        self.patch.start()
        self.screen = unittest.mock.MagicMock()

    def tearDown(self):
        super().tearDown()
        self.patch.stop()

    def test_load(self):
        img.load('title_card', self.screen)

    def test_draw(self):
        image = img.load('title_card', self.screen)
        image.draw()
        self.screen.blit.assert_called_once()

    def test_collidepoint(self):
        image = img.load('title_card', self.screen)
        self.assertTrue(image.collidepoint((0, 0)))
        self.assertFalse(image.collidepoint((-1, -1)))

    def test_position(self):
        image = img.load('title_card', self.screen, (-1, -1))
        self.assertTrue(image.collidepoint((-1, -1)))

    def test_shift(self):
        image = img.load('title_card', self.screen, shift=(1, 1))
        self.assertFalse(image.collidepoint((0, 0)))


if __name__ == '__main__':
    unittest.main()
