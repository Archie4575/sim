"""
Kinderdrome Simulation GUI
"""
import arcade
import random
from mathutils import *



# Window Constants
SCREEN_TITLE = "The Kinderdrome"
SCREEN_HEIGHT = 720
SCREEN_WIDTH = 1280
NUM_KINDER = 25

class Kinder (arcade.Sprite):
    """Kinder entity class"""
    def __init__(self, spritefile = "images/dummy.png", scaling = 1):
        super().__init__(spritefile, scaling)
        self.velocity = rand_direction()

    def update(self):
        """Update the position of the sprite"""
        super().update()

        if self.isOut(): # move to center if the edge is hit
            self.center_x, self.center_y = SCREEN_WIDTH//2, SCREEN_HEIGHT//2

        curr_direction = vel2dir(self.velocity)
        self.velocity = rand_direction(curr_direction - 10, curr_direction + 10, 'uniform')

    def isOut(self):
        return self.bottom < 0 or self.top > SCREEN_HEIGHT or self.left < 0 or self.right > SCREEN_WIDTH

class Sim(arcade.Window):
    """
    Main Simulation Class
    """

    def __init__(self):
        
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable = False)

        self.kinder_list = arcade.SpriteList()



    def setup(self):
        arcade.set_background_color( (244, 235, 208) ) #F4EBD0 (Off-White)
        
        for n in range(NUM_KINDER):
            kinder = Kinder()
            kinder.center_x = SCREEN_WIDTH * random.random() 
            kinder.center_y = SCREEN_HEIGHT * random.random()
            self.kinder_list.append(kinder)
        

    def on_update(self, delta_time):
        self.kinder_list.update()

    def on_draw(self):
        arcade.start_render()
        self.kinder_list.draw()


def main():
    sim = Sim()
    sim.setup()
    arcade.run()

if __name__ == "__main__":
    main()
