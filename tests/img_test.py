"""Tests for escape.img."""

from escape import img
import unittest
import unittest.mock
from . import test_utils


class LoadTest(test_utils.ImgTestCase):

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


class PngFactoryTest(test_utils.ImgTestCase):

    def test_factory(self):

        class MockImage(img.PngFactory):
            def __init__(self, screen):
                super().__init__('title_card', screen)

        image = img.load(self.screen, factory=MockImage)
        self.assertIsInstance(image, MockImage)


if __name__ == '__main__':
    unittest.main()
