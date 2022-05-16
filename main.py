"""
Kinderdrome Simulation GUI

Author: Archer Fabling
Version: 0.5.1
License: GNU GPL
"""

import arcade
import random
import os
import mathutils
from perlin_noise import PerlinNoise


# Window Constants
SCREEN_TITLE = "The Kinderdrome"
SCREEN_HEIGHT = 720
SCREEN_WIDTH = 1280
MARGIN = 2
BMARGIN = 50 # Margin in which blocks don't spawn
NUM_KINDER = 5
NUM_BLOCKS = 2
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
    def __init__(self, rows: int = 9, columns: int = 16):
        """Constructor"""
        spritefile = os.path.join(os.path.split(__file__)[0], 'images/floor.png') # Form absolute path
        scaling = 1
        super().__init__(spritefile, scaling)

        self.left = 0
        self.bottom = 0

        self.rows = rows
        self.columns = columns
        self.division = self.width // self.columns # Width of a square

        self.matrix = [[[] for c in range(columns)] for r in range(rows)] # Initialise empty matrix

    def update(self):
        """Checks for two kinder objects in the same cell before randomly picking one to contest another"""
        if Kinder.mode == 1:
            for r, row in enumerate(self.matrix):
                for c, cell in enumerate(row):        
                    uncontested = [k for k in cell if not k.inContest]
                    if uncontested.__len__() > 1:
                        self.print_matrix()
                        cell.pop().contest(random.choice(cell)) # Last Kinder in list contest a random Kinder in the cellx

    def print_matrix(self):
        """Prints the grid matrix"""
        for row in self.matrix[::-1]:
            for c in row:
                print("[", end='')
                for i in c:
                    try:
                        print(i._id, " ", end='')
                    except:
                        print('0', end='')
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


class Block (arcade.Sprite):
    block_count = 0

    def __init__(self):
        """Constructor"""
        spritefile = os.path.join(os.path.split(__file__)[0], 'images/blocks.png') 
        startx = random.uniform(BMARGIN, SCREEN_WIDTH - BMARGIN) # Random x within block margins 
        starty = random.uniform(BMARGIN, SCREEN_HEIGHT - BMARGIN) # Random y within block margins
        super().__init__(spritefile, scale=1, center_x = startx, center_y = starty)
        # Owner attribute
        self.owner = None
        Block.block_count += 1

    def draw(self):
        """Draw functions"""
        if self.owner: # don't draw if block has an owner,
            return
        super().draw()

        
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

    count = 0
    grid = Grid(9,16)

    def __init__(self, spritefile = "images/dummy.png", scaling = SCALING):
        """Constructor"""
        super().__init__(spritefile, scaling)
        # Give Kinder integer id based on how many Kinder have been spawned
        Kinder.count += 1
        self._id = Kinder.count
        # Spawn at random position
        self.left = MARGIN + (SCREEN_WIDTH - 2 * MARGIN - self.width - 1) * random.random()
        self.bottom = MARGIN + (SCREEN_HEIGHT - 2 * MARGIN - self.height - 1) * random.random()
        # Set movement parameters
        self.speed = 2
        self.velocity = self.new_velocity(mathutils.rand_direction())
        self.traj_vel = self.velocity
        self.traj_dir = mathutils.vel2dir(self.traj_vel)
        self.run_timer = 0
        # Contest variables
        self.inContest = False
        self.contest_timer = 0
        # Perlin noise generator
        self.t = 0
        self.perlin = PerlinNoise(octaves=self.speed/2, seed=random.randint(1,1000))
        # Define hit box
        self.set_hit_box([(24,24), (-24,24), (-24,-24), (24,-24)])
        # Initialise list of blocks
        self.blocks = []
        self.score = 0
        # Initialise ScoreLabel object
        self.label = ScoreLabel(self)

    def update(self, delta_time):
        """Update the position of the sprite"""

        if self.mode == 0:
            self.update_velocity()
        elif self.mode == 1:
            if self.inContest:
               self.contest_timer -= 1
               if self.contest_timer == 30:
                   self.traj_vel = mathutils.opposite(self.traj_vel)
                   self.velocity = self.traj_vel
               elif self.contest_timer <= 0:
                   self.inContest = False
            else:
                self.update_velocity()
        
        if self.mode == 0:
            for block in arcade.check_for_collision_with_list(self, Sim.blocks_list):
                if block.owner:
                    continue
                self.pickup(block)

        super().update()

        self.label.update()


        self.add_to_grid()

    def draw(self):
        super().draw()

        self.label.digit_sprites.draw()

        # arcade.draw_text(str(self.score), 
        #         start_x = self.left,
        #         start_y = self.top + 2,
        #         color = (220, 0, 0),
        #         font_size=10,
        #         width = self.width,
        #         align = 'center',
        #         font_name = 'Kenney Rocket')
    
    def pickup(self, block: Block):
        """Picks up the block"""
        block.owner = self
        block.position = (-50, -50) # move off screen to prevent further collisions
        self.blocks.append(block)

        self.score += 1
        Block.block_count -= 1
        if Block.block_count == 0: # If no blocks left..
            Kinder.mode = 1 # Enter Block Saturation mode
            print("Entering \"Block Saturation\" mode")

    def add_to_grid(self):
        """Adds self to Kinder.grid.matrix"""
        grid_pos = self.grid.get_grid_pos(self)
        self.grid.matrix[grid_pos[0]][grid_pos[1]].append(self)

    def update_velocity(self):
        """Updates velocity in a random walk pattern."""
        if self.isOut('x'):                                                 # If out of xbounds
            self.run_timer = 5                                              # run for 3 frames
            if self.left < MARGIN:
                self.left = MARGIN + 1
            elif self.right > SCREEN_WIDTH - MARGIN:
                self.right = SCREEN_WIDTH - MARGIN - 1
            self.traj_vel[0] = - self.traj_vel[0]                           # and horizontal trajectory
            self.velocity[0] = - self.velocity[0]                           # negate horizontal velocity
        if self.isOut('y'):                                                 # Same for ybounds
            self.run_timer = 5
            if self.bottom < 0:
                self.bottom = MARGIN + 1
            elif self.top > SCREEN_HEIGHT - MARGIN:
                self.top = SCREEN_HEIGHT - MARGIN - 1
            self.traj_vel[1] = - self.traj_vel[1]
            self.velocity[1] = - self.velocity[1]

        if self.run_timer == 0:                                             # If not running from boundaries, move normally
            new_dir = self.traj_dir + next(self.noise()) * 360              # get new direction
            self.velocity = self.new_velocity(new_dir)                      # set velocity
            if random.random() < (1/120):
                self.traj_vel = self.velocity
                self.t = random.randrange(0,10)
        else:                                                               # If still running, continue running
            self.run_timer -= 1


    def contest(self, opp):
        """Contest function, usually called by the grid, takes another Kinder.
        Initiates the block snatching process.
        
        :param Kinder opp: the opponent Kinder
        """

        # Yet to implement
        # if type(opp) != Kinder:
        #    throw ContestError

        # Face towards each other
        self.point_to_sprite(opp)
        opp.point_to_sprite(self)

        # Halt movement
        self.stop()
        opp.stop()

        # Set bools and timers
        self.inContest, opp.inContest = True, True
        self.contest_timer, opp.contest_timer = 90, 90



    def point_to_sprite(self, sprite: arcade.Sprite):
        coords = sprite.position # == (center_x, center_y)
        disp_vector = [dest - curr for dest, curr in zip(coords, self.position)]
        new_vector = self.new_velocity(mathutils.vel2dir(disp_vector))
        self.velocity = new_vector
        self.traj_dir = self.velocity
        

    def new_velocity(self, direction):
        return [v*self.speed for v in mathutils.dir2vel(direction)]

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
        return mathutils.vel2dir(self.traj_vel)

    @traj_dir.setter
    def traj_dir(self, direction):
        """traj_dir setter method"""
        return direction

    def noise(self):
        """Perlin noise generator function"""
        self.t += 1/200 * self.speed # Needs rethinking in terms of FPS
        yield self.perlin(self.t)
        

class ScoreLabel ():
    font_file = os.path.join(os.path.split(__file__)[0], 'images/digits.png')
    digit_width = 18
    digit_height = 10

    def __init__(self, parent: Kinder, score: int = 0):
        self.parent = parent
        
        self.digit_sprites = arcade.SpriteList()

        self.set_digits(0)
        self._lastscore = 0

        self.update()
    
    def update(self):
        if self.score != self._lastscore:
            self.set_digits(self.score) 
        self.update_digit_positions()
        self.digit_sprites.draw()

    def set_digits(self, score):
        self.digit_sprites.clear()

        for digit in str(score):
            self.digit_sprites.append( Digit(int(digit)) )
        
    @property
    def score(self):
        return self.parent.score
    
    def update_digit_positions(self):
        num = len(self.digit_sprites)
        label_width = self.digit_width * num
        start_y = self.parent.top + 1
        start_x = self.parent.left + ((self.parent.width - label_width) / 2)
        
        for index, digit in enumerate(self.digit_sprites):
            digit.bottom = start_y
            digit.left = start_x + index * self.digit_width

            
class Digit (arcade.Sprite):

    def __init__(self, value: int = 0):
        x, y = value * ScoreLabel.digit_width, 0
        super().__init__(ScoreLabel.font_file,
                scale = 1,
                image_x = x,
                image_y = y,
                image_width = ScoreLabel.digit_width,
                image_height = ScoreLabel.digit_height)


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

    blocks_list = arcade.SpriteList()
    kinder_list = arcade.SpriteList()

    def __init__(self, width = SCREEN_WIDTH, height = SCREEN_HEIGHT, title = SCREEN_TITLE):
        """Constructor"""
        super().__init__(width, height, title, resizable = False)

        self.paused = False
        self.framecount = 0


    def setup(self):
        """Constructor"""
        arcade.set_background_color( (244, 235, 208) )  # F4EBD0 (Off-White)

        sprites = self.get_kinder_sprites()             # Load sprite filenames
        for _ in range(NUM_KINDER):                     # Populate with Kinder objects
            kinder = Kinder(random.choice(sprites))
            self.kinder_list.append(kinder)

        for _ in range(NUM_BLOCKS):                     # Populate with Block objects
            block = Block()
            self.blocks_list.append(block)
        
#        Kinder.mode = 1

    def on_update(self, delta_time):
        """Update function"""
        if self.paused:
            return

        self.framecount += 1
        Kinder.grid.clear()
        for kinder in self.kinder_list:
            kinder.update(delta_time)
        Kinder.grid.update() # Check for contests and clear grid

    def on_key_press(self, symbol, modifiers):
        if symbol == arcade.key.SPACE:
            Kinder.grid.print_matrix()
            self.paused = not self.paused
        

    def on_draw(self):
        """Draw function"""
        arcade.start_render()
        Kinder.grid.draw()
        for block in self.blocks_list:
            block.draw()
        for kinder in self.kinder_list:
           kinder.draw()
        # self.kinder_list.draw()

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
