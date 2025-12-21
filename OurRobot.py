from jetbot import Robot
import time

robot = Robot()

TURN_SPEED = 0.1
DRIVE_SPEED = 0.119
SECONDS_PER_DEGREE = 0.01

def drive_forward(robot, duration):
    robot.set_motors(DRIVE_SPEED, DRIVE_SPEED+ 0.0065)
    time.sleep(duration)
    robot.stop()

def drive_backward(robot, duration):
    robot.set_motors(-DRIVE_SPEED, -DRIVE_SPEED)
    time.sleep(duration)
    robot.stop()

def turn_left(robot, degrees):
    turn_time = abs(degrees) * SECONDS_PER_DEGREE
    robot.set_motors(-TURN_SPEED, TURN_SPEED)
    time.sleep(abs(turn_time))
    robot.stop()

def turn_right(robot, degrees):
    turn_time = degrees * SECONDS_PER_DEGREE
    robot.set_motors(TURN_SPEED, -TURN_SPEED)
    time.sleep(abs(turn_time))
    robot.stop()