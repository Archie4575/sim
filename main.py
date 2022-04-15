"""
Kinderdrome Simulation GUI
"""
import arcade

# Window Constants
SCREEN_TITLE = "The Kinderdrome"
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

class Sim(arcade.Window):
    """
    Main Simulation Class
    """

    def __init__(self):
        
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable = False)

        arcade.background = arcade.load_texture("checkers.png")

    def setup(self):
        pass
        
    def on_update(self, delta_time):
        pass

    def on_draw(self):
        self.clear()


def main():
    window = Sim()
    arcade.run()

if __name__ == "__main__":
    main()
