"""
Kinderdrome Simulation GUI

Author: Archer Fabling
Version: 0.3.3
License: GNU GPL
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
MARGIN = 2
NUM_KINDER = 2
SCALING = 1
FPS = 60
MODES = {
    "block-surplus": 0,
    "block-saturation": 1,
    "nap_time": 2,
}

class Grid (arcade.Sprite):
    """Grid class. A static background sprite that has a matrix of cells containing the Kinder objects currently
    in said grid area. i.e. If two Kinder objects has center_x and center_y coordinates that lie within the same
    grid area, their objects will be in the same matrix cell. This is useful for initialising a contest for 
    mode 1 (block saturation).
    
    :param int rows: numbers of rows
    :param int columns: number of columns
    
    Attributes:
        :matrix: matrix of cells containing Kinder objects
        :division: side length of one grid square in pixels
    """
    def __init__(self, rows: int = 9, columns: int = 12):
        """Constructor"""
        spritefile = os.path.join(os.path.split(__file__)[0], 'images/checkers.png') # Form absolute path
        scaling = 1
        super().__init__(spritefile, scaling)

        self.left = 0
        self.bottom = 0

        self.rows = rows
        self.columns = columns
        self.division = self.width // self.rows # Width of a square

        self.matrix = [[[] for c in range(columns)] for r in range(rows)] # Initialise empty matrix

    def update(self):
        """Checks for two kinder objects in the same cell and prints if a contest is found.
        Subsequently clears the matrix for the next update."""
        for r, row in enumerate(self.matrix):
            for c, cell in enumerate(row):
                if cell.__len__() > 1:
                    print(f"Contest in cell: [{r},{c}]")
        self.clear()

    def print_matrix(self):
        """Prints the grid matrix"""
        for row in self.matrix[::-1]:
            for c in row:
                print("[", end='')
                for i in c:
                    print(i, " ", end='')
                print("]", end='')
            print()
        return
    
    def get_grid_pos(self, sprite: arcade.Sprite):
        """Returns grid area coordinated. Grid coordinates are of the form [row, column], 
        with grid cooridinate [0,0] being the bottom left-most grid square."""
        r = int(sprite.center_y // self.division)
        c = int(sprite.center_x // self.division)

        return [r,c]

    def clear(self):
        """Clears the matrix"""
        self.matrix = [[[] for c in range(self.columns)] for r in range(self.rows)]



        

class Kinder (arcade.Sprite):
    """Kinder class. Runs around the room and responds to stimuli.
        
    :param str spritefile: absolute path to sprite image
    :param float scaling: sprite scale factor

    Attributes:
        :velocity: rectangular vector of floats
        :traj_vel: intial velocity and the direction from which the velocity deviates
        :traj_dir: angle of the traj_vel
        :speed: number of pixels moved every update
        :run_timer: framecount timer for running from boundaries
        :perlin: perlin noise generator
        :t: starting value for perlin noise generator
    """

    mode = 0
    """Modes:
    0 - Block surplus
    1 - Block saturation
    2 - Naptime
    """

    grid = Grid(9,16)

    def __init__(self, spritefile = "images/dummy.png", scaling = SCALING):
        """Constructor"""
        super().__init__(spritefile, scaling)
        # Spawn at random position
        self.left = MARGIN + (SCREEN_WIDTH - 2 * MARGIN - self.width - 1) * random.random()
        self.bottom = MARGIN + (SCREEN_HEIGHT - 2 * MARGIN - self.height - 1) * random.random()
        # Set movement parameters
        self.velocity = rand_direction()
        self.traj_vel = deepcopy(self.velocity)
        self.traj_dir = vel2dir(self.traj_vel)
        self.speed = 2
        self.run_timer = 0
        # Perlin noise generator
        self.t = 0
        self.perlin = PerlinNoise(octaves=self.speed/2, seed=random.randint(1,1000))
        # Define hit box
        self.set_hit_box([(24,24), (-24,24), (-24,-24), (24,-24)])

    def update(self, delta_time):
        """Update the position of the sprite"""

        if self.mode == 0 or self.mode == 1:                                    # Block surplus or block saturation
            if self.isOut('x'):                                                 # If out of xbounds
                self.run_timer = 5                                              # run for 3 frames
                self.velocity[0] = - self.velocity[0]                           # negate horizontal velocity
                self.traj_vel[0] = - self.traj_vel[0]                           # and horizontal trajectory
            if self.isOut('y'):                                                 # Same for ybounds
                self.run_timer = 5
                self.velocity[1] = - self.velocity[1]
                self.traj_vel[1] = - self.traj_vel[1]

            if self.run_timer == 0:                                             # If not running from boundaries, move normally
                unit_vel = dir2vel(self.traj_dir + next(self.noise()) * 360)    # get new direction
                final_vel = [v*self.speed for v in unit_vel]                    # scale it based on self.speed
                self.velocity = final_vel                                       # set velocity
            else:                                                               # If still running, continue running
                self.run_timer -= 1

        super().update()

        self.add_to_grid()

    def add_to_grid(self):
        grid_pos = self.grid.get_grid_pos(self)
        self.grid.matrix[grid_pos[0]][grid_pos[1]].append(self)

    def isOut(self, mode = None):
        """Is sprite hit box out of bounds. Returns Boolean
        
        :mode: the coordinates to check
            Defaults to none.
            Use 'x' to check left and right bounds.
            Use 'y' to check top and bottom bounds.
        """

        outx = (self.left < MARGIN or self.right > (SCREEN_WIDTH - MARGIN))
        outy = (self.bottom < MARGIN or self.top > (SCREEN_HEIGHT - MARGIN))

        if mode == 'x':
            return outx
        if mode == 'y':
            return outy
        else:
            return outx or outy
        
    @property
    def traj_dir(self):
        """traj_dir getter method"""
        return vel2dir(self.traj_vel)

    @traj_dir.setter
    def traj_dir(self, direction):
        """traj_dir setter method"""
        return direction

    def noise(self):
        """Perlin noise generator function"""
        self.t += 1/200 * self.speed # Needs rethinking in terms of FPS
        yield self.perlin(self.t)
    
class Sim(arcade.Window):
    """
    Main Simulation Class

    :param int width: Window width
    :param int height: Window hieght
    :param str title: Window title

    Attributes:
        :kinder_list: SpriteList of Kinder objects
        :block_list: SpriteList of Block objects
    """

    def __init__(self, width = SCREEN_WIDTH, height = SCREEN_HEIGHT, title = SCREEN_TITLE):
        """Constructor"""
        super().__init__(width, height, title, resizable = False)

        self.block_list = arcade.SpriteList()
        self.kinder_list = arcade.SpriteList()


    def setup(self):
        """Constructor"""
        arcade.set_background_color( (244, 235, 208) )  # F4EBD0 (Off-White)
        
        sprites = self.get_kinder_sprites()             # Load sprite filenames
        for _ in range(NUM_KINDER):                     # Populate with Kinder objects
            kinder = Kinder(random.choice(sprites))
            self.kinder_list.append(kinder)
        

    def on_update(self, delta_time):
        """Update function"""
        for kinder in self.kinder_list:
            kinder.update(delta_time)
        Kinder.grid.update() # Check for contests and clear grid

    def on_draw(self):
        """Draw function"""
        arcade.start_render()
        Kinder.grid.draw()
        self.kinder_list.draw()

    def get_kinder_sprites(self):
        """Return absolute paths of image files in images/kinder"""
        main_dir = os.path.split(__file__)[0]
        sprite_dir = os.path.join(main_dir, "images/kinder")
        try:
            images = os.listdir(sprite_dir)
        except FileNotFoundError as err:
            raise FileNotFoundError(f"Could not find sprite folder: '{sprite_dir}'. \
                Are you running from the right directory?")

        # filter for .png or .jpg files
        images = [image for image in images if os.path.splitext(image)[1] in ['.jpg', '.jpeg', '.png']]
        if len(images) == 0:
            raise Exception("No kinder sprite images found in ./images/kinder")
        # form full paths
        paths = [os.path.join(sprite_dir, image) for image in images]

        return paths


def main():
    sim = Sim(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
    sim.setup()
    sim.set_update_rate(1/FPS)
    arcade.run()

if __name__ == "__main__":
    main()
