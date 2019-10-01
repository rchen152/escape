"""Image handling."""

import os
import pygame


class _Image:

    def __init__(self, name, screen, position=(0, 0), shift=(0, 0)):
        """Initializer for a png image.

        Args:
          name: The name of the image without the png extension.
          screen: The screen to draw the image on.
          position: The position of the image's top-left corner.
          shift: A tuple of factors of the width and height to shift the
            position by.
        """

        path = os.path.join(os.path.dirname(__file__), 'img', f'{name}.png')
        self._img = pygame.image.load(path).convert_alpha()
        self._screen = screen
        self._pos = (position[0] + self._img.get_width() * shift[0],
                     position[1] + self._img.get_height() * shift[1])

    def draw(self):
        self._screen.blit(self._img, self._pos)

    def collidepoint(self, pos):
        return pygame.Rect(self._pos, self._img.get_size()).collidepoint(pos)


def load(*args, **kwargs):
    return _Image(*args, **kwargs)
