"""
Kinderdrome Simulation GUI
"""
import arcade
import random
import os
from mathutils import *
from copy import deepcopy


# Window Constants
SCREEN_TITLE = "The Kinderdrome"
SCREEN_HEIGHT = 720
SCREEN_WIDTH = 1280
MARGIN = 0
NUM_KINDER = 25
SCALING = 1
MODES = {
    "block-surplus": 0,
    "block-saturation": 1,
}



class Kinder (arcade.Sprite):
    """Kinder entity class"""
    mode = 0
    """modes:
        0 - Block surplus
        1 - Block saturation
        2 - Naptime"""

    def __init__(self, spritefile = "images/dummy.png", scaling = SCALING):
        super().__init__(spritefile, scaling)
        self.left = MARGIN + (SCREEN_WIDTH - 2 * MARGIN - self.width - 1) * random.random()
        self.bottom = MARGIN + (SCREEN_HEIGHT - 2 * MARGIN - self.height - 1) * random.random()
        self.velocity = rand_direction()
        self.traj_vel = deepcopy(self.velocity)
        self.traj_dir = vel2dir(self.traj_vel)
        self.speed = 2
        self.t = 0
        self.run_timer = 0
        self.perlin = PerlinNoise(octaves=self.speed/2, seed=random.randint(1,1000))
        self.set_hit_box([(20,20), (-20,20), (-20,-20), (20,-20)])

    def update(self):
        """Update the position of the sprite"""
        
        self.draw_hit_box(arcade.color.RED, 15)

        if self.isOut('x'):                                                 # If out of xbounds
            self.run_timer = 5                                              # run for 3 frames
            self.velocity[0] = - self.velocity[0]                           # negate horizontal velocity
            self.traj_vel[0] = - self.traj_vel[0]                           # and horizontal trajectory
        if self.isOut('y'):                                                 # Same for ybounds
            self.run_timer = 5
            self.velocity[1] = - self.velocity[1]
            self.traj_vel[1] = - self.traj_vel[1]

        if self.run_timer == 0:                                             # If not running from boundaries, move normally
            unit_velocity = dir2vel(self.traj_dir + next(self.noise()) * 360) # get new direction
            speed_velocity = [v*self.speed for v in unit_velocity]  # scale it based on self.speed
            self.velocity = speed_velocity                                  # set velocity
        else:                                                               # If still running, continue running
            self.run_timer -= 1

        super().update()


    def isOut(self, mode = None):
        if mode == 'x':
            return (self.left < MARGIN or self.right > (SCREEN_WIDTH - MARGIN))
        if mode == 'y':
            return (self.bottom < MARGIN or self.top > (SCREEN_HEIGHT - MARGIN))
        else:
            return (self.bottom < MARGIN or self.top > (SCREEN_HEIGHT - MARGIN) or self.left < MARGIN or self.right > (SCREEN_WIDTH - MARGIN))
        
    @property
    def traj_dir(self):
        return vel2dir(self.traj_vel)

    @traj_dir.setter
    def traj_dir(self, direction):
        return direction

    def noise(self):
        self.t += 1/200 * self.speed
        yield self.perlin(self.t)
    
class Sim(arcade.Window):
    """
    Main Simulation Class
    """

    def __init__(self):
        
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable = False)

        self.kinder_list = arcade.SpriteList()
        self.block_list = arcade.SpriteList()


    def setup(self):
        arcade.set_background_color( (244, 235, 208) ) #F4EBD0 (Off-White)
        
        sprites = self.get_kinder_sprites()
        for n in range(NUM_KINDER):
            kinder = Kinder(random.choice(sprites))
            self.kinder_list.append(kinder)
        

    def on_update(self, delta_time):
        self.kinder_list.update()

    def on_draw(self):
        arcade.start_render()
        self.kinder_list.draw()

    def get_kinder_sprites(self):
        sprite_dir = "images/kinder"
        try:
            images = os.listdir(sprite_dir)
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Could not find sprite folder: '{sprite_dir}'. \
                Are you running from the right directory?")

        # filter for .png files
        images = [image for image in images if os.path.splitext(image)[1] in ['.jpg', '.png']]
        if len(images) == 0:
            raise Exception("No kinder sprite images found in ./images/kinder")
        # form full paths
        paths = [os.path.join(sprite_dir, image) for image in images]

        return paths


def main():
    sim = Sim()
    sim.setup()
    arcade.run()

if __name__ == "__main__":
    main()
