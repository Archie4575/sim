The Kinderdrome
===============
Author: Archer Fabling  
Contact:  <20885436@student.curtin.edu.au>  
GitHub: https://github.com/Archie4575  

## Synopsis

A simulation of kindergarten kids running around a classroom and picking up blocks.  
The simulation has several modes:  
- Block Surplus - Kindergarteners meander and collect blocks upon collision  
- Block Saturation - Kindergarteners start to contest ecah other and snatch each others' blocks when all blocks have been collected.  
- Nap Time - All kindergarteners drop their blocks and find a place to rest.   

In a contest between two kindergarteners, the kindergartener with the most blocks has a better chance of winning the contest. This is designed to simulate a system of inequal distribution where the rich get richer and should, if ran long enough, produce a Pareto distribution of blocks in which the top 20% of kinders have accumulated approximately 80% of the blocks. To test this, statistics about the distribution of wealth are printed to standard out every time the nap-time is entered by the user and the economy of blocks is reset. 

## Installation

Clone the repository:
>`git clone https://github.com/Archie4575/sim.git`  
>`cd sim`  

Install the packages on Linux and Windwos:  
>`python3 -m pip install -r requirements.txt`  

Or if using MacOS:  
>`python3 -m pip install -r requirements_macos.txt`  

## Usage

Run the simulation:
>`python3 main.py`

### Options:  

*\*work in progress\**

## Content

- README.md - README file  
- requirements.txt - pip package dependencies for Linux and Windows  
- requirements_macos.txt - pip package dependencies for MacOS (includes PyObjC)  
- main.py - main simulation code and class definitions  
- mathutils.py - related math functions  
- images/ - image resources  
    - checkers.png - black and white checkered grid 
    - floor.png - wood tiled floor
    - digits.png - light blue digits 0 to 9 in Kenney Rocket font for score labels
    - dummy.png - 40x40 dummy sprite  
    - blocks.png - pile of blocks sprite
    - kinder/ - sprite image files (extensible, sprite files and paths are reloaded from disk every simulation)

## Dependencies

Found in `requirements.txt` (or `requirements_macos.txt` for Mac users)

## Version Information
0.0.1 - 14/04/2022 - Initialisation  
0.0.2 - 15/04/2022 - Inital idle figure using the `arcade` package  
0.1.0 - 25/04/2022 - Uniform and Gaussian random walk implemented  
0.1.1 - 25/04/2022 - Updated the README  
0.2.0 - 25/04/2022 - Implemented perlin walk and boundary bouncing  
0.2.1 - 25/04/2022 - `README.md` formatting  
0.2.2 - 25/04/2022 - Added timmy.png and images/kinder sub-directory  
0.2.3 - 25/04/2022 - Added `requirements.txt` file  
0.3.0 - 28/04/2022 - Implemented extensible set of kinder sprites  
0.3.1 - 28/04/2022 - Set FPS and made spritefile paths absolute  
0.3.2 - 28/04/2022 - Docstrings and Python 3.6 compatability  
0.3.3 - 29/04/2022 - Updated `README.md`  
0.4.0 - 30/04/2022 - Implemented basic grid framework  
0.4.1 - 04/05/2022 - Implemented contest model, sim framecount, and kinder ids  
0.4.2 - 10/05/2022 - Updated packages  
0.5.0 - 11/05/2022 - Implemented `Block` objects  
0.5.1 - 12/05/2022 - Fixing speed for score labels and updated README
0.5.2 - 16/05/2022 - Added Digits and ScoreLabel objects and Grid and Block textures
0.5.3 - 17/05/2022 - New Docstrings
0.5.4 - 17/05/2022 - Change to Grid.print_matrix() and Kinder boundary collisions