"""Test utilities."""

import pygame
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
