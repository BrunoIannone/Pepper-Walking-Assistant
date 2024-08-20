import qi
import argparse
import sys
import time
import random
import math
import os


# ------------------------- Joint values for postures ------------------------ #

joint_limits = {
    'HeadYaw': (-2.0857, 2.0857),
    'HeadPitch': (-0.7068, 0.6371),
    'LShoulderPitch': (-2.0857, 2.0857),
    'LShoulderRoll': (0.0087, 1.5620),
    'LElbowYaw': (-2.0857, 2.0857),
    'LElbowRoll': (-1.5620, -0.0087),
    'LWristYaw': (-1.8239, 1.8239),
    'RShoulderPitch': (-2.0857, 2.0857),
    'RShoulderRoll': (-1.5620, -0.0087),
    'RElbowYaw': (-2.0857, 2.0857),
    'RElbowRoll': (0.0087,1.5620),
    'RWristYaw': (-1.8239, 1.8239)
}

left_arm_raised = {
    'LShoulderRoll': 1.5620,
    'LElbowYaw': -1.5,
    'LElbowRoll': -1.5,
    'LWristYaw': -0.5
}

right_arm_raised = {
    'RShoulderRoll': -1.5620,
    'RElbowYaw': 1.5,
    'RElbowRoll': 1.5,
    'RWristYaw': 0.5,
}

default_posture = {
    'HeadYaw': 0.0,
    'HeadPitch': -0.2,
    'LShoulderPitch': 1.5,
    'LShoulderRoll': 0.1,
    'LElbowYaw': -1.2,
    'LElbowRoll': -0.5,
    'LWristYaw': 0.0,
    'RShoulderPitch': 1.6,
    'RShoulderRoll': -0.1,
    'RElbowYaw': 1.2,
    'RElbowRoll': 0.5,
    'RWristYaw': 0.0
}


# --------------------------------- Services --------------------------------- #

global as_service # Animated Speech
global bm_service # Behavior Manager
global ap_service # Animation Player
global mo_service # Motion
global me_service # Memory
global to_service # Touch


# --------------------------------- Variables -------------------------------- #

# State to track if the hand has been touched
global hand_touched
hand_touched = False

# The robot is using either the left or the right hand
global hand_picked
hand_picked = 'Left'

# Target coordinates
global x, y

# ---------------------------------- Methods --------------------------------- #


def asay(sentence):
    """
    Say something while contextually moving the head as you speak 
    """

    global as_service 
    configuration = {"bodyLanguageMode":"contextual"}
    as_service.say(sentence, configuration)


def perform_animation(animation, _async=True):
    """
    Perform a predefined animation. The animation should be visible by the behavior_manager 
    among the installed behaviors, otherwise it is silently discarded 
    """

    # List all available animations
    global bm_service, ap_service
    behaviors = bm_service.getInstalledBehaviors()
    
    if animation in behaviors:    
        ap_service.run(animation, _async=_async)


def perform_movement(joint_values, speed=1.0, _async=True):
    """
    Perform the motion specified by the provided joint values. Joint values 
    should be in the allowed range, otherwise the value is silently discarded
    """

    global mo_service
    mo_service.setStiffnesses('Body', 1.0)

    for joint_name, joint_value in joint_values.items():
        if joint_limits[joint_name][0] <= joint_value <= joint_limits[joint_name][1]:
            mo_service.setAngles(joint_name, joint_value, speed, _async=_async)


def on_hand_touched(_name, _value, _subscriber_identifier):
    global hand_touched
    hand_touched = True

    asay("Let's begin!")

    global me_service
    me_service.unsubscribeToEvent("Hand" + hand_picked + "BackTouched", "on_hand_touched")
    mo_service.post.moveTo(x, y, 0)


def on_hand_released(_name, _value, _subscriber_identifier):
    
    # asay("Would you like to cancel?")
    asay("Are you sure you want to cancel?")
    
    global mo_service, me_service
    mo_service.stopMove()
    me_service.unsubscribeToEvent("Hand" + hand_picked + "BackReleased", "on_hand_released")


# Deprecated
def wait_for_touch(timeout=20.0):
    """
    Wait for #timeout that the user touches pepper's hand. If the hand 
    is not touched after the timeout, return False, otherwise return True
    """

    global to_service

    start_time = time.time()
    while time.time() - start_time < timeout:
        touched = to_service.getStatus()
        for sensor in touched:
            if sensor[0] == hand_picked[0] + "HandTouch" and sensor[1] == True:
                return True
        time.sleep(0.1)  # Polling interval

    return False


def procedure(target_room):

    # Establish if the robot has to move left or right
    global hand_picked
    if target_room[0] > 0:
        # The robot has to move right, raise left hand
        hand_picked = "Left"
    else:
        # The robot has to move left, raise right hand
        hand_picked = "Right"

    # Raise the respective arm (async)
    perform_movement(joint_values=left_arm_raised if hand_picked == 'Left' else right_arm_raised, speed=0.25)

    # Give instructions to the user while the hand is raising
    asay("Hold my left hand and I'll guide you there!")

    # Subscribe to the touch and release events
    me_service.subscribeToEvent("Hand" + hand_picked + "BackTouched", "on_hand_touched", "")
    me_service.subscribeToEvent("Hand" + hand_picked + "BackReleased", "on_hand_released", "")
    
    # Wait for the touch or timeout
    time.sleep(20)  # Giving the user 20 seconds to touch the hand
    
    if not hand_touched:
        asay("No touch detected.")

    # Else, ask if the user would like to cancel the procedure
    asay("Would you like to cancel the procedure?")

    # Yes: return


    # No: procedure again
    perform_movement(default_posture)


def get_room(room_id):
    """
    Given a room_id, returns the coordinates of the room to reach.
    This should be replaced by a more complex logic accounting for 
    walls, stairs and so on. For our purposes this stub is more than
    enough 
    """

    # Generate a random point where to go to simulate the target room
    angle = random.uniform(0, math.pi)
    distance = 1.0
    
    x = distance * math.cos(angle)
    y = distance * math.sin(angle)
    
    return x, y


def main():

    # Retrieve arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--pip", type=str, default=os.environ['PEPPER_IP'],
                        help="Robot IP address.  On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--pport", type=int, default=9559,
                        help="Naoqi port number")
    args = parser.parse_args()
    pip = args.pip
    pport = args.pport

    # Starting application
    try:
        connection_url = "tcp://" + pip + ":" + str(pport)
        app = qi.Application(["Memory Read", "--qi-url=" + connection_url ])
    except RuntimeError:
        print ("Can't connect to Naoqi at ip \"" + pip + "\" on port " + str(pport) +".\n"
               "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    app.start()
    session = app.session

    # Initialize the services
    global as_service, bm_service, ap_service, mo_service, to_service, me_service
    as_service = session.service("ALAnimatedSpeech")
    bm_service = session.service("ALBehaviorManager")
    ap_service = session.service("ALAnimationPlayer")
    mo_service = session.service("ALMotion")
    me_service = session.service("ALMemory")
    to_service = session.service("ALTouch")

    # Greet the user
    # perform(animation="demo_animations/animations/Hey_1")

    room_id = "room_1"
    room_coords = get_room(room_id)
    procedure(room_coords)


if __name__ == "__main__":
    main()
