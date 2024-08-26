import qi
import argparse
import sys
import time
import random
import math
import os

from automata import State, TimeoutState, FiniteStateAutomaton

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
    'RElbowRoll': (0.0087, 1.5620),
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
    'HeadPitch': -0.21,
    'LShoulderPitch': 1.55,
    'LShoulderRoll': 0.13,
    'LElbowYaw': -1.24,
    'LElbowRoll': -0.52,
    'LWristYaw': 0.01,
    'RShoulderPitch': 1.56,
    'RShoulderRoll': -0.14,
    'RElbowYaw': 1.22,
    'RElbowRoll': 0.52,
    'RWristYaw': -0.01
}

# --------------------------------- Services --------------------------------- #

global as_service  # Animated Speech
global bm_service  # Behavior Manager
global ap_service  # Animation Player
global mo_service  # Motion
global me_service  # Memory
global to_service  # Touch
global na_service  # Navigation
# global sr_service # Speech Recognition

# --------------------------------- Variables -------------------------------- #

# The robot is using either the left or the right hand
global hand_picked
hand_picked = 'Left'

# Finite state automata
global automaton

# Signals
global touch_subscriber  #, word_subscriber

# Current and target position
global current_x, current_y
global target_x, target_y
current_x = 0
current_y = 0


# ---------------------------------- States ---------------------------------- #

class SteadyState(TimeoutState):

    def __init__(self, automaton, timeout=10):
        super(SteadyState, self).__init__('steady_state', automaton, timeout=timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(SteadyState, self).on_enter()
        print("[INFO] Entering Steady State")

        # Behavior

        perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        global hand_picked
        animated_say("Grab my " + hand_picked + " hand and I'll guide you there!")
        print('[INFO] Talking: Grab my ' + hand_picked + " hand and I'll guide you there!")

        perform_movement(joint_values=left_arm_raised if hand_picked == 'Left' else right_arm_raised, speed=0.25)
        print("[INFO] Raising " + hand_picked.lower() + " hand")

    def on_event(self, event):
        super(SteadyState, self).on_event(event)
        if event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class MovingState(State):
    def __init__(self, automaton):
        super(MovingState, self).__init__('moving_state', automaton)

    def on_enter(self):
        super(MovingState, self).on_enter()
        print('[INFO] Entering Moving State')

        # Behavior
        global target_x, target_y
        global current_x, current_y
        theta = math.atan2(target_y - current_y, target_x - current_x)
        move_to(target_x, target_y, theta)
        print('[INFO] Moving to: ' + str(target_x) + ', ' + str(target_y))

    def on_event(self, event):
        super(MovingState, self).on_event(event)
        if event == 'hand_released':
            stop_motion()
            self.automaton.change_state('ask_state')


class QuitState(State):

    def __init__(self, automaton):
        super(QuitState, self).__init__('quit_state', automaton)

    def on_enter(self):
        super(QuitState, self).on_enter()
        print('[INFO] Entering Quit State')

        # Go back to default position
        perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        # Unsubscribe from signals
        # global touch_subscriber, word_subscriber, sr_service
        # sr_service.unsubscribe("pepper_walking_assistant_ASR")
        # word_subscriber.signal.disconnect()
        # touch_subscriber.signal.disconnect()

        print("[INFO] Done")


class HoldHandState(TimeoutState):

    def __init__(self, automaton, timeout=10):
        super(HoldHandState, self).__init__('hold_hand_state', automaton, timeout=timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(HoldHandState, self).on_enter()
        print('[INFO] Entering Hold Hand State')

        # Behavior
        animated_say("Grab my hand to continue!")
        print('[INFO] Talking: Grab my hand to continue!')

    def on_event(self, event):
        super(HoldHandState, self).on_event(event)
        if event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class AskState(TimeoutState):

    def __init__(self, automaton, timeout=10):
        super(AskState, self).__init__('ask_state', automaton, timeout=timeout, timeout_event='steady_state')

    def on_enter(self):
        super(AskState, self).on_enter()
        print("[INFO] Entering Ask State")

        # Behavior
        animated_say("Do you want to cancel?")
        print('[INFO] Talking: Do you want to cancel?')

        # TODO remove user response simulation
        on_word_recognized(None)

    def on_event(self, event):
        super(AskState, self).on_event(event)
        if event == 'response_yes':
            self.automaton.change_state('quit_state')
        elif event == 'response_no':
            self.automaton.change_state('hold_hand_state')
        elif event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


# ------------------------------ Utility methods ----------------------------- #

def animated_say(sentence):
    """
    Say something while contextually moving the head as you speak 
    """
    global as_service
    configuration = {"bodyLanguageMode": "contextual"}
    as_service.say(sentence, configuration)


def perform_animation(animation, _async=True):
    """
    Perform a predefined animation. The animation should be visible by the behavior_manager 
    among the installed behaviors, otherwise it is silently discarded 
    """
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


def move_to(x, y, theta):
    """
    Move the robot to the specified target position and orientation.

    This function uses ALNavigation.navigateTo for movement to (x, y) coordinates
    and ALMotion.moveTo for the final orientation adjustment.

    Parameters:
    x (float): Target X coordinate in meters (in FRAME_WORLD).
    y (float): Target Y coordinate in meters (in FRAME_WORLD).
    theta (float): Target orientation in radians (in FRAME_WORLD).

    Returns:
    bool: True if the robot successfully reached the target, False otherwise.

    Note:
    - The maximum distance for a single navigateTo call is 3 meters.
    - This function updates the global current_x and current_y variables.
    """
    global na_service, current_x, current_y

    try:
        # Calculate relative movement
        delta_x = x - current_x
        delta_y = y - current_y

        # Use navigateTo for movement
        success = na_service.navigateTo(delta_x, delta_y)

        if success:
            # Update current position if movement was successful
            current_x, current_y = x, y

            # Rotate to the desired orientation
            mo_service.moveTo(0, 0, theta)

            print(f"[INFO] Moved to position: ({x}, {y}) with orientation {theta}")
        else:
            print("[INFO] Navigation failed or was interrupted")

        return success
    except Exception as e:
        print(f"[ERROR] Failed to move: {e}")
        return False


def stop_motion():
    """
    Stop the robot's motion and update the current location.

    This function uses ALMotion.stopMove() to halt the robot's movement
    and then updates the global current_x and current_y variables with
    the robot's final position.

    Note:
    - This function updates the global current_x and current_y variables.
    """
    global mo_service, me_service, current_x, current_y
    try:
        # Stop the robot
        mo_service.stopMove()

        # Get the current position
        robot_pose = mo_service.getRobotPosition(True)
        current_x, current_y = robot_pose[0], robot_pose[1]

        print(f"[INFO] Motion stopped. Current position: ({current_x}, {current_y})")
    except Exception as e:
        print(f"[ERROR] Failed to stop motion: {e}")


# --------------------------------- Callbacks -------------------------------- #

def on_hand_touch_change(value):
    """
    Callback function triggered when the hand touch event occurs.
    Dispatch the event to the automata.
    """
    global hand_picked, automaton
    print("[INFO] " + hand_picked + " hand touch value changed: " + str(value))
    if value == 0.0:
        automaton.on_event('hand_released')
    else:
        automaton.on_event('hand_touched')


def on_word_recognized(value):
    """
    Callback function triggered when a word is recognized.
    Dispatch the event to the automata.
    """

    """
    recognized_word = value[0] if value else ""
    print("[INFO] Recognized word: ", recognized_word)
    
    global automaton
    if recognized_word == "yes":
        automaton.on_event('response_yes')
    elif recognized_word == "no":
        automaton.on_event('response_no')
    else:
        print("[INFO] Response not recognized")
    """

    time.sleep(random.randint(2, 4))

    global automaton
    if random.random() > 0.5:
        print('[USER] Response: yes')
        automaton.on_event('response_yes')
    else:
        print('[USER] Response: no')
        automaton.on_event('response_no')


# ----------------------------------- Main ----------------------------------- #

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pip", type=str, default=os.environ['PEPPER_IP'],
                        help="Robot IP address.  On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--pport", type=int, default=9559,
                        help="Naoqi port number")
    parser.add_argument("--coords", type=float, nargs=2, metavar=('X', 'Y'), default=[1.0, 1.0],
                        help="Target coordinates")
    args = parser.parse_args()
    pip = args.pip
    pport = args.pport

    # Starting application
    try:
        connection_url = "tcp://" + pip + ":" + str(pport)
        app = qi.Application(["Memory Read", "--qi-url=" + connection_url])
    except RuntimeError:
        print("Can't connect to Naoqi at ip \"" + pip + "\" on port " + str(pport) + ".\n"
              "Please check your script arguments. Run with -h option for help.")
        sys.exit(1)
    app.start()
    session = app.session

    # Initialize the services
    global as_service, bm_service, ap_service, mo_service, me_service  #, sr_service
    as_service = session.service("ALAnimatedSpeech")
    bm_service = session.service("ALBehaviorManager")
    ap_service = session.service("ALAnimationPlayer")
    mo_service = session.service("ALMotion")
    me_service = session.service("ALMemory")
    # sr_service = session.service("ALSpeechRecognition")

    # Establish which hand to use
    global target_x, target_y
    target_x, target_y = args.coords
    print("[INFO] Target position: " + str(target_x) + ", " + str(target_y))

    global hand_picked
    hand_picked = 'Right' if target_x < 0 else 'Left'

    # Create the automata
    global automaton
    automaton = FiniteStateAutomaton()

    steady_state = SteadyState(automaton)
    moving_state = MovingState(automaton)
    ask_state = AskState(automaton, timeout=10)
    hold_hand_state = HoldHandState(automaton, timeout=10)
    quit_state = QuitState(automaton)

    automaton.add_state(steady_state)
    automaton.add_state(moving_state)
    automaton.add_state(ask_state)
    automaton.add_state(hold_hand_state)
    automaton.add_state(quit_state)

    automaton.start('steady_state')

    # Connect the pepper event callbacks to the automaton
    global touch_subscriber  #, word_subscriber

    touch_event = "Hand" + hand_picked + "BackTouched"
    touch_subscriber = me_service.subscriber(touch_event)
    touch_subscriber.signal.connect(on_hand_touch_change)

    """
    sr_service.setLanguage("English")
    sr_service.setVocabulary(["yes", "no"], False)
    sr_service.subscribe("pepper_walking_assistant_ASR")  # Start the speech recognition engine with user pepper_walking_assistant_ASR
    word_subscriber = me_service.subscriber("WordRecognized") # Subscribe to event WordRecognized
    word_subscriber.signal.connect(on_word_recognized)
    """

    # Program stays at this point until we stop it
    app.run()


if __name__ == "__main__":
    main()
