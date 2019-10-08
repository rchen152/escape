"""Test utilities."""

import pygame
from pygame.locals import *
import unittest.mock


class MockImg:

    def __init__(self, real_img):
        self._real_img = real_img

    def convert_alpha(self):
        return self

    def __getattr__(self, name):
        return getattr(self._real_img, name)


class PygameImagePatch:

    def __init__(self, *args, **kwargs):
        self._patch = unittest.mock.patch('pygame.image', *args, **kwargs)
        self._real_load = pygame.image.load

    def mock_load(self, path):
        real_img = self._real_load(path)
        return MockImg(real_img)

    def __enter__(self):
        mock_image_mod = self._patch.__enter__()
        mock_image_mod.load = self.mock_load
        return mock_image_mod

    def __exit__(self, *exc_info):
        return self._patch.__exit__(*exc_info)

    def start(self):
        return self.__enter__()

    def stop(self):
        return self.__exit__()


def patch(module, *args, **kwargs):
    """Like unittest.mock.patch but with special handling for pygame.image."""
    if module == 'pygame.image':
        return PygameImagePatch(*args, **kwargs)
    return unittest.mock.patch(module, *args, **kwargs)


class MockEvent:

    def __init__(self, typ, **kwargs):
        self.type = typ
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockScreen:

    def __init__(self):
        self.fullscreen = False
        self.mock = unittest.mock.MagicMock()

    def get_flags(self):
        return FULLSCREEN if self.fullscreen else 0

    def __getattr__(self, name):
        return getattr(self.mock, name)


class ImgTestCase(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.patch = patch('pygame.image')
        self.patch.start()
        self.screen = MockScreen()

    def tearDown(self):
        super().tearDown()
        self.patch.stop()
