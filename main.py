"""Точка входа. Запуск: python main.py (нужен установленный pygame: pip install pygame)"""
import pygame

from ui import WIDTH, HEIGHT
from states import MenuState


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Турнир школ стихий — прототип")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("arial", 40, bold=True)
        self.font = pygame.font.SysFont("arial", 24)
        self.font_small = pygame.font.SysFont("arial", 18)

        self.players = []
        self.state = None
        self.set_state(MenuState(self))
        self.running = True

    def set_state(self, state):
        self.state = state

    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.state.handle_event(event)
            self.state.update(dt)
            self.state.draw(self.screen, self.font_big, self.font, self.font_small)
            pygame.display.flip()
        pygame.quit()


if __name__ == "__main__":
    Game().run()
