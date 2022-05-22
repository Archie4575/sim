#!/usr/bin/env python3
"""
Kinderdrome Simulation GUI

Author: Archer Fabling
Version: 0.9.0
License: GNU GPL
"""

from math import sqrt
import random
SEED = "naughty"
random.seed(a = SEED, version=2)  # For Reproducability while bug-fixing
import os
import mathutils
import argparse

try:
    import arcade
    from perlin_noise import PerlinNoise
    import matplotlib.pyplot as plt
except ModuleNotFoundError as err:
    print(err)
    print("The right modules haven't been installed yet.\n Try running \
\"python3 -m pip install -r requirements.txt\" to install the correct \
pacakages. (use \"requirements_macos.txt\" on Mac)")
    exit()

def abs_path(relative_path):
    """Returns of absolute path given a path relative to this file."""
    return os.path.join(os.path.split(__file__)[0], relative_path)


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
        spritefile = abs_path('images/floor.png')  # Form absolute path
        scaling = 1
        super().__init__(spritefile, scaling)

        self.left = 0
        self.bottom = 0

        self.rows = rows
        self.columns = columns
        self.division = self.width // self.columns  # Width of a square

        self.matrix = [[[] for c in range(columns)] for r in range(rows)]  # Initialise empty matrix

    def update(self):
        """Checks for two kinder objects in the same cell before randomly picking one to contest another"""
        if Kinder.mode == 1:
            for r, row in enumerate(self.matrix):
                for c, cell in enumerate(row):
                    uncontested = [k for k in cell if not k.inContest]
                    if uncontested.__len__() > 1:
                        cell = [k for k in cell if k.score > 0]  # Filter out those who have none
                        if len(cell) > 0:
                            first_contestant = cell.pop()  # Pick one kinder
                            candidates = [kinder for kinder in cell if kinder != first_contestant.last_contested] # Filter so two kinder can't contest twice in a row
                            if first_contestant.score == 1:  # Filters so two 1's don't contest each other
                                candidates = [kinder for kinder in candidates if kinder.score > 1]
                            if len(candidates) > 0:
                                first_contestant.contest(random.choice(candidates))  # Contest a random valid Kinder candidate

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
        spritefile = abs_path('images/blocks.png') 
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


class Bed (arcade.Sprite):
    """Bed class.""" 
    def __init__(self, row, col):
        super().__init__(abs_path("images/vacant_bed.png"), scale = 1)
        self.textures.append(arcade.load_texture("images/vacant_bed.png",
                hit_box_algorithm = "Simple",
                hit_box_detail=4.5,
            )
        )
        self.isFull = False
        self.set_pos(row, col)

    def update(self):
        if self.isFull:
            self.set_texture(1)
        else:
            self.set_texture(0)

        super().__init__()

    def set_pos(self, row, col):
        div = Kinder.grid.division
        self.center_y = div * (row + 0.5)
        self.center_x = div * (col + 0.5)

 
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
    snatch_amount = 2

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
        # Contest variables
        self.isSnatcher = False
        self.last_contested = None
        # Initialise ScoreLabel object
        self.label = ScoreLabel(self)
        # Bed variables
        self.isAsleep = False

    def update(self, delta_time):
        """Update the position of the sprite"""
        self.collide_with_margins()

        if self.mode == self.MODES['block_surplus']:
            self.update_velocity()
        elif self.mode == self.MODES['block_saturation']:
            if self.inContest:
               self.contest_timer -= 1
               if self.contest_timer == 30:
                   if self.isSnatcher:
                       self.snatch(self.opponent)
                       self.isSnatcher = False
                   self.traj_vel = mathutils.opposite(self.traj_vel)
                   self.velocity = self.traj_vel
               elif self.contest_timer <= 0:
                   self.inContest = False
                   self.last_contested = self.opponent
            else:
                self.update_velocity()
        
        if self.mode == self.MODES['block_surplus']:
            for block in arcade.check_for_collision_with_list(self, Sim.blocks_list):
                if block.owner:
                    continue
                self.pickup(block)
        
        if self.mode == self.MODES['nap_time'] and not self.isAsleep:
            if Sim.last_num_beds != Sim.num_beds:
                bed = self.find_nearest_bed(Sim.available_bed_list)
                self.point_to_sprite(bed)
            collisions = arcade.check_for_collision_with_list(self, Sim.available_bed_list)
            if collisions:
                self.take_bed(collisions[0])


        super().update()
        self.add_to_grid()

    def draw(self):
        """Draw function. Draws the sprite then their scoreLabels"""
        super().draw()
        self.label.update()
    
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

    def pickup(self, block: Block):
        """Picks up the block"""
        block.owner = self
        print(f"Kinder #{self._id} picked up a block. \tScore = {self.score} \tRemaining = {Block.block_count}")
        block.position = (-50, -50) # move off screen to prevent further collisions
        self.blocks.append(block)
        Sim.blocks_list.remove(block)

        self.score += 1
        Block.block_count -= 1
        if Block.block_count == 0: # If no blocks left..
            Kinder.mode = Kinder.MODES["block_saturation"] 
            print("Zero blocks left! Entering \"Block Saturation\" mode!")

    def contest(self, opp):
        """Contest function, usually called by the grid, takes another Kinder.
        Initiates the block snatching process.
        
        :param Sprite opp: the opponent Kinder
        """
        # Face towards each other
        self.point_to_sprite(opp)
        opp.point_to_sprite(self)

        # Set each other as opponents
        self.opponent = opp
        opp.opponent = self

        # Halt movement
        self.stop()
        opp.stop()

        # Set bools and timers
        self.inContest, opp.inContest = True, True
        self.contest_timer, opp.contest_timer = 90, 90

        # Pick which Kinder will win the contest
        # Method 1: A has a 70% change of getting 70% of B's blocks, is A has 7 and B has 3
        winchance = self.score/(self.score+opp.score)

        if random.random() < winchance:
            self.isSnatcher = True
            opp.isSnatcher = False
        else:
            opp.isSnatcher = True
            self.isSnatcher = False

    def snatch(self, victim):
        """Snatch function, used in contests.
        
        :param Kinder victim: victim of snatch
        :param int amount: number of blocks to be snatched
        """
        amount = round((self.score/(self.score+victim.score))*(victim.score))

        snatched = 0
        for _ in range(amount):
            if victim.score > 1:
                self.blocks.append(victim.blocks.pop()) # Pop from their stack, push to yours
                self.score += 1
                snatched += 1
                victim.score -= 1

        # Update labels
        self.label.update()
        victim.label.update()

        # Log transaction
        print(f"#{self._id} snatched {snatched} blocks from #{victim._id}")  

    def find_nearest_bed(self, bedlist):
        displacements = [ (bed, (self.center_x - bed.center_x,
                self.center_y - bed.center_y)) for bed in bedlist]
        distances = [(n, sqrt(pow(s[1][0],2) + pow(s[1][1],2))) for n, s in enumerate(displacements)]
        min_index = min(distances, key = lambda distance: distance[1])[0]
        closest_path = displacements[min_index]
        closest_bed = closest_path[0]

        return closest_bed

    def drop_blocks(self):
        print(self.blocks)
        for block in self.blocks:
            self.score -= 1
            print("-1")
            block.owner = None
            block.position = mathutils.rand_point_in_circle(center = self.position, radius = self.grid.division)
            Sim.blocks_list.append(block)
            Block.block_count += 1
        self.blocks.clear()
        self.label.update()
        print("score: ", self.score)

    def take_bed(self, bed):
        bed.isFull = True
        Sim.available_bed_list.remove(bed)
        Sim.num_beds -= 1
        self.isAsleep = True
        self.velocity = (0,0)
        self.position = bed.position
    
    def awake(self):
        self.isAsleep = False

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
    font_file = abs_path('images/digits_black.png')
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
        elif self.score == 0:
            self.set_digits()
        self.update_digit_positions() # Position digits above the parent sprite
        self.digit_sprites.draw()

    def set_digits(self, score=''):
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


class HUD (arcade.Sprite):
    """Heads Up Display. Overalay to show controls."""

    def __init__(self):
        starter_hud = abs_path("images/HUD.png")
        super().__init__(starter_hud, scale=1)
        self.textures.append(arcade.load_texture(
                abs_path("images/HUDP.png"),
                x=0,
                y=0,
                width=1280,
                height=720,
                flipped_horizontally=False,
                flipped_vertically=False,
                flipped_diagonally=False,
                hit_box_algorithm="Simple",
                hit_box_detail=4.5,
            )
        )
        self.left = 0
        self.bottom = 0
        self.pause = False
    
    def update(self):
        """Update function. Toggles between textures 0 and 1"""
        self.pause = not self.pause
        self.set_texture(int(self.pause))


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
    bed_list = arcade.SpriteList()
    available_bed_list = arcade.SpriteList()
    last_num_beds = 0
    num_beds = 0

    SCREEN_TITLE = "The Kinderdrome"
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    MARGIN = 4
    FPS = 60
    framecount = 0

    data_snapshots = {}
    last_data_snapshot = None

    def __init__(self, args):
        """Constructor"""
        super().__init__(self.SCREEN_WIDTH, self.SCREEN_HEIGHT, self.SCREEN_TITLE, resizable = False)

        self.numkinder = args.numkinder
        self.numblocks = args.numblocks
        self.runtime = args.runtime
        self.quiet = args.quiet

        self.paused = False

        self.hud = HUD()

    def setup(self):
        """Constructor"""
        arcade.set_background_color((0,0,0))

        sprites = self.get_kinder_sprites()  # Load sprite filenames
        for n in range(self.numkinder):  # Populate with Kinder objects
            kinder = Kinder(sprites[n % len(sprites)])  # Create even distribution of sprites
            self.kinder_list.append(kinder)

        for _ in range(self.numblocks):  # Populate with Block objects
            block = Block()
            self.blocks_list.append(block)
        
    def on_update(self, delta_time):
        """Update function"""
        if self.paused:
            return

        self.framecount += 1
        if self.framecount == self.FPS * self.runtime:
            self.exit()

        self.last_num_beds = self.num_beds

        Kinder.grid.clear()
        for kinder in self.kinder_list:
            kinder.update(delta_time)
        Kinder.grid.update()  # Check for contests 

    def on_key_press(self, symbol, modifiers):
        """Triggered by key press event"""
        if symbol == arcade.key.SPACE:
            self.pause()

        if symbol == arcade.key.Q:
            self.exit()
        
        if symbol == arcade.key.N:
            if Kinder.mode == Kinder.MODES['nap_time']:  # From nap time to normal
                Kinder.mode = Kinder.MODES['block_surplus'] 
                self.bed_list.clear()
                self.available_bed_list.clear()
                for kinder in self.kinder_list:
                    kinder.awake()
            else:                                        # Form normal to nap time
                Kinder.mode = Kinder.MODES['nap_time']
                self.spawn_beds()
                self.data_snapshots[self.framecount] = self.get_data()
                self.last_data_snapshot = self.data_snapshots[self.framecount]
                for kinder in self.kinder_list:
                    kinder.drop_blocks()
                    print("dropping")
                print("printing")
                self.print_last_stats()
                print("printed")

    def pause(self):
        self.paused = not self.paused
        self.hud.update()

    def exit(self):
        self.close()
        arcade.exit()
        if Kinder.mode == Kinder.MODES['nap_time']:
            self.print_last_stats()
        else:
            self.print_stats()

    def on_draw(self):
        """Draw function"""
        arcade.start_render()
        Kinder.grid.draw()
        self.bed_list.draw()
        for block in self.blocks_list:
            block.draw()
        for kinder in self.kinder_list:
           kinder.draw()
        self.hud.draw()

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

    def spawn_beds(self):
        # Sides first
        for col in [0,15]:
            for row in range(9):
                if self.num_beds == self.numkinder: return
                bed = Bed(row, col)
                self.bed_list.append(bed)
                self.available_bed_list.append(bed)
                self.num_beds += 1
        
        # Then top
        for row in [0,8]:
            for col in range(1,15):
                if self.num_beds == self.numkinder: return
                bed = Bed(row, col)
                self.bed_list.append(bed)
                self.available_bed_list.append(bed)
                self.num_beds += 1

    def get_data(self):
        if self.kinder_list:
            return {k._id: k.score for k in self.kinder_list}
        else:
            return None

    def print_stats(self, data = None):
        if data == None:
            data = self.get_data()
            self.data_snapshots[self.framecount] = data
            self.last_data_snapshot = data

        print(self.twenty_eighty(data))


        if not self.quiet:
            self.generate_bar_graph(data)
        
    def print_last_stats(self):
        if self.last_data_snapshot:
            self.print_stats(self.last_data_snapshot)
        else:
            self.print_stats()

    def generate_bar_graph(self, data: dict):
        """Generates a bar graph with Kinder IDs along the x-axis and their respective score on the y-axis.
        
        :param dict data: data in dictionary form
        """
        ranked_data = {rank + 1: datapoint for rank, datapoint in enumerate(sorted(data.items(), key=lambda item: item[1])[::-1])}
        xvalues = list(ranked_data.keys())
        yvalues = [datapoint[1] for rank, datapoint in ranked_data.items()]
        labels = [datapoint[0] for rank, datapoint in ranked_data.items()]

        title = f"Block Distribution at Frame Count {self.framecount}, Kinder={self.numkinder}, Blocks={self.numblocks}"
        filename = f"chart-k{self.numkinder}-b{self.numblocks}-f{self.framecount}"

        if SEED:
            title += f"\n[SEED={SEED}]"

        with plt.style.context(('dark_background')):
            plt.figure(1)
            plt.bar(x=xvalues, height=yvalues, data=labels)
            plt.ylabel("Blocks")
            plt.xlabel("Rank")
            plt.title(title)
            plt.savefig(f"output/{filename}")
            plt.show()

    def twenty_eighty(self, data: dict):
        sorted_items = list(sorted(data.items(), key = lambda item: -item[1]))  # Sorts items by value
        
        number_in_top = int(round(len(sorted_items) * 0.20))   # multiplys and rounds
        top = sorted_items[:number_in_top]  # Top twenty percentage

        total = sum([item[1] for item in sorted_items])
        top_total = sum([item[1] for item in top])

        percentile = number_in_top/len(sorted_items)
        share = top_total/total

        result = f"The top {percentile*100}% of Kindergarteners have {share*100}% of the Blocks."
        return result


def main():
    parser = argparse.ArgumentParser(description="Kinderdrome simulation using python arcade package")
    parser.add_argument("-k", "--numkinder", type=int, default=20, metavar='INT', help="Number of Kindergarteners to spawn. Default=20")
    parser.add_argument("-b", "--numblocks", type=int, default=100, metavar='INT', help="Number of Blocks to spawn. Default=40")
    parser.add_argument("-t", "--runtime", type=int, default=0, metavar='INT', help="Seconds to run the simulation for. Default=0 (infinite)")
    parser.add_argument("-q", "--quiet", action="store_true", default=False, help="Suppress statistics graph at the end of the runtime.")
    args = parser.parse_args()

    sim = Sim(args)
    sim.setup()
    sim.set_update_rate(1/Sim.FPS)

    arcade.run()    

if __name__ == "__main__":
    main()