from jetbot import Robot
import time

robot = Robot()

TURN_SPEED = 0.4
DRIVE_SPEED = 0.1
SECONDS_PER_DEGREE = 0.012

def drive_forward(robot, duration):
    robot.set_motors(DRIVE_SPEED, DRIVE_SPEED)
    time.sleep(duration)
    robot.stop()

def drive_backward(robot, duration):
    robot.set_motors(-DRIVE_SPEED, -DRIVE_SPEED)
    time.sleep(duration)
    robot.stop()

def turn_left(robot, degrees):
    turn_time = degrees * SECONDS_PER_DEGREE
    robot.set_motors(-TURN_SPEED, TURN_SPEED)
    time.sleep(turn_time)
    robot.stop()

def turn_right(robot, degrees):
    turn_time = degrees * SECONDS_PER_DEGREE
    robot.set_motors(TURN_SPEED, -TURN_SPEED)
    time.sleep(turn_time)
    robot.stop()