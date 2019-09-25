"""Main entrypoint."""
import pygame
from . import state


def main():
    pygame.init()
    screen = pygame.display.set_mode(state.WINSIZE)
    pygame.display.set_caption('Kitty Escape')
    state.TitleCard(screen).run()
    state.Game(screen).run()


if __name__ == '__main__':
    main()
