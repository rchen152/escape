"""Main entrypoint."""
import pygame
from . import state


def main():
    pygame.init()
    pygame.display.set_mode(state.WINSIZE)
    pygame.display.set_caption('Kitty Escape')
    game_state = state.GameState()

    while game_state.active:
        game_state.handle_events(pygame.event.get())


if __name__ == '__main__':
    main()
