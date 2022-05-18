#!/usr/bin/env python3
"""
Kinderdrome Simulation GUI

Author: Archer Fabling
Version: 0.6.0
License: GNU GPL
"""

try:
    import arcade
    from perlin_noise import PerlinNoise
except ModuleNotFoundError as err:
    print(err)
    print("The right modules haven't been installed yet.\nTry running \"python3 -m pip install -r requirements.txt\" to install the correct pacakages. (use \"requirements_macos.txt\" on Mac)")
    exit()

import random
import os
import mathutils
import argparse

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
        for ridx, row in enumerate(self.matrix[::-1]):
            print(ridx, " [", end='')
            for c in row:
                print(f"{len(c)}", end="")
            print("]")
        print()
    
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
    """Block class. Spawned on at a random position on the ground and is collected by Kinder.
    
    Attributes:
        :Kinder owner: Defaults to none, changes when block is picked up."""
    block_count = 0 # Number of blocks on the ground
    BMARGIN = 50

    def __init__(self):
        """Constructor"""
        spritefile = os.path.join(os.path.split(__file__)[0], 'images/blocks.png') 
        startx = random.uniform(self.BMARGIN, Sim.SCREEN_WIDTH - self.BMARGIN) # Random x within block margins 
        starty = random.uniform(self.BMARGIN, Sim.SCREEN_HEIGHT - self.BMARGIN) # Random y within block margins
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
    MODES = {
        "block_surplus": 0,
        "block_saturation": 1,
        "nap_time": 2,
        }

    count = 0
    grid = None

    def __init__(self, spritefile = "images/dummy.png", scaling = 1):
        """Constructor"""
        super().__init__(spritefile, scaling)
        # Initailise the grid
        if not Kinder.grid: 
            Kinder.grid = Grid()
        # Give Kinder integer id based on how many Kinder have been spawned
        Kinder.count += 1
        self._id = Kinder.count
        # Spawn at random position
        self.left = Sim.MARGIN + (Sim.SCREEN_WIDTH - 2 * Sim.MARGIN - self.width - 1) * random.random()
        self.bottom = Sim.MARGIN + (Sim.SCREEN_HEIGHT - 2 * Sim.MARGIN - self.height - 1) * random.random()
        # Set movement parameters
        self.speed = 2
        self.velocity = self.new_velocity(mathutils.rand_direction())
        self.traj_vel = self.velocity
        self.traj_dir = mathutils.vel2dir(self.traj_vel)
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
        self.collide_with_margins()

        if self.mode == self.MODES['block_surplus']:
            self.update_velocity()
        elif self.mode == self.MODES['block_saturation']:
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
        self.add_to_grid()

    def draw(self):
        """Draw function. Draws the sprite then their scoreLabels"""
        super().draw()
        self.label.update()

    def pickup(self, block: Block):
        """Picks up the block"""
        block.owner = self
        print(f"Kinder #{self._id} picked up a block. \tScore = {self.score} \tRemaining = {Block.block_count}")
        block.position = (-50, -50) # move off screen to prevent further collisions
        self.blocks.append(block)

        self.score += 1
        Block.block_count -= 1
        if Block.block_count == 0: # If no blocks left..
            Kinder.mode = Kinder.MODES["block_saturation"] 
            print("Zero blocks left! Entering \"Block Saturation\" mode!")

    def add_to_grid(self):
        """Adds self to Kinder.grid.matrix"""
        try:
            grid_pos = self.grid.get_grid_pos(self)
            self.grid.matrix[grid_pos[0]][grid_pos[1]].append(self)
        except IndexError as err:
            raise Exception(f"Kinder #{self._id} (Score: {self.score}) is not on grid.\nPosition = {self.position}")

    def update_velocity(self):
        """Updates velocity in a random walk pattern using perlin noise"""

        new_dir = self.traj_dir + next(self.noise()) * 360              # get new direction
        self.velocity = self.new_velocity(new_dir)                      # set velocity
        if random.random() < (1/120):
                self.traj_vel = self.velocity
                self.t = random.randrange(0,10)

    def contest(self, opp):
        """Contest function, usually called by the grid, takes another Kinder.
        Initiates the block snatching process.
        
        :param Sprite opp: the opponent Kinder
        """
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
        """Sets the velocity to point to a given sprite
        
        :param Sprite sprite: the sprite to point to
        """
        coords = sprite.position # == (center_x, center_y)
        disp_vector = [dest - curr for dest, curr in zip(coords, self.position)]
        new_vector = self.new_velocity(mathutils.vel2dir(disp_vector))
        self.velocity = new_vector
        self.traj_dir = self.velocity
        
    def new_velocity(self, direction):
        """Takes a direction and returns a velocity with the correct speed
        
        :param float direction: direction of new velocity
        """
        return [v*self.speed for v in mathutils.dir2vel(direction)]

    def collide_with_margins(self):
        """Is sprite hit box out of bounds? Returns Boolean
        
        :mode: the coordinates to check
            Defaults to none.
            Use 'x' to check left and right bounds.
            Use 'y' to check top and bottom bounds.
        """
        CENTER_MARGIN = Sim.MARGIN + self.width / 2 # Margin relative to the center of the sprite
        SCREEN_WIDTH = Sim.SCREEN_WIDTH
        SCREEN_HEIGHT = Sim.SCREEN_HEIGHT

        if self.center_x < CENTER_MARGIN:
            self.center_x = CENTER_MARGIN + 1
            self.traj_vel[0] *= -1
        if self.center_x > SCREEN_WIDTH - CENTER_MARGIN:
            self.center_x = SCREEN_WIDTH - CENTER_MARGIN - 1
            self.traj_vel[0] *= -1

        if self.center_y < CENTER_MARGIN:
            self.center_y = CENTER_MARGIN + 1
            self.traj_vel[1] *= -1
        if self.center_y > SCREEN_HEIGHT - CENTER_MARGIN:
            self.center_y = SCREEN_HEIGHT - CENTER_MARGIN - 1
            self.traj_vel[1] *= -1
        
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
    """ScoreLabel object. Assigned to a parent Kinder at construction and assigned a score to display.
    Manages and updates a list of Digit objects which are shown on screen above the sprite.
    
    :param Kinder parent: Kinder that this label pertains to
    
    Attributes:
        :digit_width: pixel width of digits in font file
        :digit_height: pixel height of digits in font file
        :parent: parent sprite
        :digit_sprites: SpriteList of Digit objects
        :score: alias for the parent Kinder's score
        :_lastscore: used to detect frame by frame changes to the score
    """
    font_file = os.path.join(os.path.split(__file__)[0], 'images/digits.png')
    digit_width = 18
    digit_height = 10

    def __init__(self, parent: Kinder):
        """Constructor"""
        self.parent = parent
        
        self.digit_sprites = arcade.SpriteList()

        self.set_digits(self.score) # populate with digits to show score of the parent
        self._lastscore = self.score

        self.update()
    
    def update(self):
        """Update function"""
        if self.score != self._lastscore: # If change in score
            self.set_digits(self.score) # Repopulate digit_sprites
        self.update_digit_positions() # Position digits above the parent sprite
        self.digit_sprites.draw()

    def set_digits(self, score):
        """Repopulates the digit sprite list with the appropriate digits"""
        self.digit_sprites.clear()

        for digit in str(score): 
            self.digit_sprites.append( Digit(int(digit)) )
        
    @property
    def score(self):
        """Alias for the parent's score"""
        return self.parent.score
    
    def update_digit_positions(self):
        """Positions list of digit sprites above the parent sprite"""
        num = len(self.digit_sprites)
        label_width = self.digit_width * num
        start_y = self.parent.top + 1
        start_x = self.parent.left + ((self.parent.width - label_width) / 2) # Centered above the sprite
        
        for index, digit in enumerate(self.digit_sprites):
            digit.bottom = start_y
            digit.left = start_x + index * self.digit_width

            
class Digit (arcade.Sprite):
    """Digit object. Sprite with digit texture.
    
    :param int value: value for the digit to represent at construction.
    """
    def __init__(self, value: int = 0):
        """Constructor"""
        super().__init__(ScoreLabel.font_file,
                scale = 1,
                image_x = value * ScoreLabel.digit_width,
                image_y = 0,
                image_width = ScoreLabel.digit_width,
                image_height = ScoreLabel.digit_height)


class Sim(arcade.Window):
    """Main Simulation Class

    :param int width: Window width
    :param int height: Window hieght
    :param str title: Window title

    Attributes:
        :kinder_list: SpriteList of Kinder objects
        :block_list: SpriteList of Block objects
    """

    blocks_list = arcade.SpriteList()
    kinder_list = arcade.SpriteList()

    SCREEN_TITLE = "The Kinderdrome"
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    MARGIN = 2
    FPS = 60

    def __init__(self, numkinder, numblocks):
        """Constructor"""
        super().__init__(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SCREEN_TITLE, resizable = False)

        self.numkinder = numkinder
        self.numblocks = numblocks
        self.paused = False
        self.framecount = 0


    def setup(self):
        """Constructor"""
        arcade.set_background_color( (244, 235, 208) )  # F4EBD0 (Off-White)

        sprites = self.get_kinder_sprites()  # Load sprite filenames
        for n in range(self.numkinder):  # Populate with Kinder objects
            kinder = Kinder(sprites[n % len(sprites)])  # Create even distribution of sprites
            self.kinder_list.append(kinder)

        for _ in range(self.numblocks):  # Populate with Block objects
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
        """Triggered by key press event"""
        if symbol == arcade.key.SPACE:
            Kinder.grid.print_matrix()
            self.pause()
        
    def pause(self):
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
        
        paths = [os.path.join(sprite_dir, image) for image in images] # form full paths

        return paths


def main():
    parser = argparse.ArgumentParser(description="Kinderdrome simulation using python arcade package")
    parser.add_argument("-k", "--numkinder", default=20, metavar='INT', help="Number of Kindergarteners to spawn. Default=20")
    parser.add_argument("-b", "--numblocks", default=40, metavar='INT', help="Number of Blocks to spawn. Default=40")
    args = parser.parse_args()

    sim = Sim(int(args.numkinder), int(args.numblocks))
    sim.setup()
    sim.set_update_rate(1/Sim.FPS)

    arcade.run()    

if __name__ == "__main__":
    main()