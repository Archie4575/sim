from math import cos, sin, radians, atan, degrees, pi
from main import SEED
import random
random.seed(a = SEED, version = 2)

def rand_direction(start: float = 0.0, stop: float = 360.0, mode: str = 'uniform', t: float = 0) -> list:
        """Random direction generator: returns random angle in degrees
        with an argument between the stop and start values (in degrees)
        
        :param float start:  lowerbound in degrees
        :param float stop:   upperbound in degrees
        :param str mode:     probability distribution function used within the interval
            'uniform' equal chance of any value
            'gaussian' bell curve distribution
        """

        lower = start
        upper = stop
        diff = upper - lower

        if diff == 0: # If difference is zero, return vector
            arg = lower
            return (round(cos(radians(arg)), 2), round(sin(radians(arg)),2))

        if diff < 0: # swap such that lower < upper
            lower, upper = upper, lower

        if mode == 'uniform': # find argument with uniform pdf
            arg = lower + random.random() * diff

        elif mode == 'gaussian': # find argument with gaussian pdf
            mean = (upper + lower) * 0.5
            stdev = diff / 4.0 # Stdev is a quarter of the range, therefore a 95% the random gaussian angle will be in range
            arg = random.gauss(mean, stdev)
            while not (lower < arg and arg < upper): # Repeat until within bounds
                arg = random.gauss(mean, stdev)

        else:
            raise Exception(f"Invalid mode: '{mode}'")

        return arg

def vel2dir(velocity: list = (1,0)) -> float:
    """Get agrument in degrees of rectangular velocity vector.
    
    :param list velocity: rectangular velocity vector
    """
    if velocity[0] != 0:
        grad = velocity[1]/velocity[0]
        arg = degrees(atan(grad))
        if velocity[0] < 0:
            arg = arg + 180
        return arg
    else:
        return 90 * (2-velocity[1]) # 90 if (0,1) and 270 if (0,-1)

def dir2vel(direction: float = 0) -> list:
    """Get rectangular unit vector from angle in degrees"""
    return [round(cos(radians(direction)),2), round(sin(radians(direction)),2)]

def opposite(velocity: list) -> float:
    """Negates all elements of a list"""
    return [-v for v in velocity]

def rand_point_in_circle(center, radius):
    angle = random.random() * 2 * pi
    distance = random.random() * radius

    dx = cos(angle) * distance
    dy = sin(angle) * distance

    point = [center[0] + dx, center[1] + dy]

    return point


if __name__ == '__main__':
    ### Testing rand_direction()
    print(rand_direction(0,360,'uniform'))
    print(rand_direction(360,360,'uniform'))
    print(rand_direction(360,0,'uniform'))
    print(rand_direction(0,90,'gaussian'))
    print(rand_direction(0,-90,'gaussian'))
    print(vel2dir((1,0)))
    print(vel2dir((-0.707,-0.707)))