import math
import threading
from datetime import datetime

from automaton import TimeoutState, State, FiniteStateAutomaton
from ..utils.limits import joint_limits
from ..utils.postures import default_posture, left_arm_raised, right_arm_raised
import time


# ---------------------------------- States ---------------------------------- #

class SteadyState(TimeoutState):

    def __init__(self, automaton, timeout=10):
        super(SteadyState, self).__init__('steady_state', automaton, timeout=timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(SteadyState, self).on_enter()
        print("[INFO] Entering Steady State")

        # Behavior

        self.automaton.perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        self.automaton.instruct()
        print('[INFO] Giving blind/deaf instructions on how to start')

        self.automaton.perform_movement(joint_values=left_arm_raised if self.automaton.arm == 'Left' else right_arm_raised, speed=0.25)
        print("[INFO] Raising " + self.automaton.arm.lower() + " hand")

    def on_event(self, event):
        super(SteadyState, self).on_event(event)
        if event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')

class MovingState(State):

    def __init__(self, automaton):
        super(MovingState, self).__init__('moving_state', automaton)

        self.current_room = None
        self.next_room = None
        self.path_index = 0

        self.theta_reached = False

        self.move_timer = None      # This timer will automatically stop the movement after the time has passed
        self.start_time = None      # When the timer started
        self.remaining_time = None  # Remaining time for the current movement

    def compute_travel_time(self):
        """
        Computes the time required to move between the current and next room.
        Assumes a constant speed. The two rooms need to be defined
        """
        if self.current_room and self.next_room:

            distance = self.current_room.distance(self.next_room)
            speed = self.automaton.action_manager.default_lin_vel
            print('[INFO] Computed distance: ' + str(distance))
            print('[INFO] Computed speed: ' + str(speed))
            print('[INFO] Computed time: ' + str(distance / speed))

            return distance / speed
        return 0

    def on_enter(self):
        super(MovingState, self).on_enter()

        self.current_room = self.automaton.position_manager.path[self.path_index]
        self.next_room = (
            self.automaton.position_manager.path[self.path_index + 1]
            if self.path_index + 1 < len(self.automaton.position_manager.path)
            else None
        )

        # Resume the movement if was paused, start a movement if it was not already started
        if self.remaining_time is None:
            self.remaining_time = self.compute_travel_time()

        print("[INFO] Entering " + str(self.name) + ". " +
              "Moving from " + str(self.current_room) + "(" + str(self.current_room.x) + ", " + str(self.current_room.y) + ")" +
              " to " + str(self.next_room) + "(" + str(self.next_room.x) + ", " + str(self.next_room.y) + "). " +
              "Remaining time: " + str(self.remaining_time)
        )

        pos = self.automaton.action_manager.mo_service.getRobotPosition(False)
        print("[INFO] Position: " + str(pos))

        robot_pose = self.automaton.action_manager.mo_service.getRobotPosition(False)
        desired_theta = math.atan2(self.next_room.y - robot_pose[1], self.next_room.x - robot_pose[0])
        distance = desired_theta - robot_pose[2]
        self.automaton.action_manager.mo_service.moveTo(0, 0, distance)
        self.start_timer(self.remaining_time)

        v_x, v_y = self.compute_linear_velocity_vector()
        self.automaton.action_manager.mo_service.move(v_x, v_y, 0)

    def on_event(self, event):
        super(MovingState, self).on_event(event)

        if event == 'room_reached':

            print('[INFO] Fired room_reached event')
            print(time.time())

            # Go to the next room
            self.path_index += 1

            # These need to be recomputed
            self.remaining_time = None
            self.start_time = None

            # Check if we reached the goal (we are now currently on the last position in the path)
            if self.path_index == len(self.automaton.position_manager.path) - 1:

                # Stop the robot
                self.automaton.action_manager.mo_service.stopMove()
                print("[INFO] Stopping the robot")

                print("[INFO] Path completed. Transitioning to GoalState.")
                self.automaton.change_state('quit_state')
            else:
                # Re-enter the same state
                self.automaton.change_state('moving_state')

        elif event == 'hand_released':

            print('[INFO] Fired hand_released event')
            print(time.time())
            # Stop the robot
            self.automaton.action_manager.mo_service.stopMove()
            print("[INFO] Stopping the robot")

            # Cancel the timer
            self.move_timer.cancel()
            self.move_timer = None
            print("[INFO] Stopping the timer")

            elapsed_time = time.time() - self.start_time
            self.remaining_time = max(self.remaining_time - elapsed_time, 0)

            self.automaton.change_state('ask_state')

    def start_timer(self, duration):
        """
        Start a timer to simulate movement and trigger the `room_reached` event.
        """

        print('[INFO] start timer')

        self.start_time = time.time()

        def trigger_event():
            self.on_event("room_reached")

        self.move_timer = threading.Timer(duration, trigger_event)
        self.move_timer.start()

    def compute_linear_velocity_vector(self):
        """
        We have the magnitude of the velocity (e.g. 0.7 m/s) and we want
        to compute the velocity vector based on the deltas in x, y directions
        """

        v_max = self.automaton.action_manager.default_lin_vel

        x_r, y_r, theta_r = self.automaton.action_manager.mo_service.getRobotPosition(False)

        # Unpack current and next points
        x_n, y_n = self.next_room.x, self.next_room.y

        # Compute the differences
        dx = x_n - x_r
        dy = y_n - y_r

        d = math.sqrt(dx ** 2 + dy ** 2)

        print('[INFO] delta_x: ' + str(dx))
        print('[INFO] delta_y: ' + str(dy))
        print('[INFO] d: ' + str(d))

        dx_robot = math.cos(-theta_r) * dx - math.sin(-theta_r) * dy
        dy_robot = math.sin(-theta_r) * dx + math.cos(-theta_r) * dy

        # Linear velocities
        if d > 0:
            # v_x = v_max * (delta_x / d)
            # v_y = v_max * (delta_y / d)
            v_x = dx_robot
            v_y = dy_robot
        else:
            v_x = 0
            v_y = 0

        print('[INFO] v_x: ' + str(v_x))
        print('[INFO] v_y: ' + str(v_y))

        return v_x, v_y

class QuitState(State):

    def __init__(self, automaton):
        super(QuitState, self).__init__('quit_state', automaton)

    def on_enter(self):
        super(QuitState, self).on_enter()
        print('[INFO] Entering Quit State')

        # Go back to default position
        self.automaton.perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        # Signaling the user we reached the target
        if self.automaton.disability == 0:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_goal)
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_goal)
        print('[INFO] Signaling the user we reached the target')

        self.automaton.release_resources()
        print('[INFO] Releasing resources')

        print("[INFO] Done")
        exit(1)

    def on_event(self, event):
        super(QuitState, self)

class HoldHandState(TimeoutState):

    def __init__(self, automaton, timeout=10):
        super(HoldHandState, self).__init__('hold_hand_state', automaton, timeout=timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(HoldHandState, self).on_enter()
        print('[INFO] Entering Hold Hand State')

        # Behavior

        self.automaton.instruct()
        print('[INFO] Giving blind/deaf instructions on how to start')

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

        if self.automaton.disability == 0:  # Blindness
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_ask_cancel)
            print('[INFO] Asking the user if he wants to cancel the procedure')
        elif self.automaton.disability == 1:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_ask_cancel)
            print('[INFO] Showing buttons for the user to choose if he wants to cancel the procedure')

        result = self.automaton.action_manager.check_status()
        print('[INFO] Obtained response: ' + result)
        self.automaton.on_event(result)  # Can be 'result_yes' or 'result_no'

    def on_event(self, event):
        super(AskState, self).on_event(event)
        if event == 'result_yes':
            self.automaton.change_state('quit_state')
        elif event == 'result_no':
            self.automaton.change_state('hold_hand_state')
        elif event == 'hand_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')


class RobotAutomaton(FiniteStateAutomaton):

    def __init__(self, modim_web_server, action_manager, position_manager, arm='Left', alevel=0):
        super(RobotAutomaton, self).__init__()
        self.modim_web_server = modim_web_server
        self.action_manager = action_manager
        self.position_manager = position_manager
        self.arm = arm
        self.alevel = alevel

        # Connect the touch event to the automata
        touch_event = "Hand" + arm + "BackTouched"
        self.touch_subscriber = self.action_manager.me_service.subscriber(touch_event)
        self.touch_id = self.touch_subscriber.signal.connect(self.on_hand_touch_change)

    # ----------------------------- Utility functions ---------------------------- #

    def on_hand_touch_change(self, value):
        """
        Callback function triggered when the hand touch event occurs.
        Dispatch the event to the automata.
        """
        print("[INFO] Hand touch value changed: " + str(value))
        if value == 0.0:
            self.on_event('hand_released')
        else:
            self.on_event('hand_touched')

    def perform_animation(self, animation, _async=True):
        """
        Perform a predefined animation. The animation should be visible by the behavior_manager 
        among the installed behaviors, otherwise it is silently discarded 
        """
        behaviors = self.action_manager.bm_service.getInstalledBehaviors()

        if animation in behaviors:
            self.action_manager.ap_service.run(animation, _async=_async)

    def perform_movement(self, joint_values, speed=1.0, _async=True):
        """
        Perform the motion specified by the provided joint values. Joint values 
        should be in the allowed range, otherwise the value is silently discarded
        """

        # Enable stiffness
        # self.action_manager.mo_service.setStiffnesses(["LArm", "RArm"], 1.0)

        # Perform movement
        for joint_name, joint_value in joint_values.items():
            if joint_limits[joint_name][0] <= joint_value <= joint_limits[joint_name][1]:
                self.action_manager.mo_service.setAngles(joint_name, joint_value, speed, _async=_async)

        time.sleep(2)

        # Disable arm stiffness during walking
        # self.action_manager.mo_service.setStiffnesses(["LArm", "RArm"], 0.5)

    def instruct(self):
        """
        Give instructions on how to start to the user. Instructions can be shown on the tablet (deaf user) 
        or said by the robot (blind user)
        """
        if self.alevel == 0:  # Blindness
            if self.arm == 'Left':
                print('[INFO] Instructing user with alevel=0 arm=Left')
                self.modim_web_server.run_interaction(self.action_manager.left_blind_walk_hold_hand)
            else:
                print('[INFO] Instructing user with alevel=0 arm=Right')
                self.modim_web_server.run_interaction(self.action_manager.right_blind_walk_hold_hand)
        elif self.alevel == 1:
            if self.arm == 'Left':
                print('[INFO] Instructing user with alevel=1 arm=Left')
                self.modim_web_server.run_interaction(self.action_manager.left_deaf_walk_hold_hand)
            else:
                print('[INFO] Instructing user with alevel=1 arm=Right')
                self.modim_web_server.run_interaction(self.action_manager.right_deaf_walk_hold_hand)
        time.sleep(2)
    
    def release_resources(self):
        self.touch_subscriber.signal.disconnect(self.touch_id)

def create_automaton(modim_web_server, action_manager, position_manager, wtime=10, arm='Left', alevel=0):
    automaton = RobotAutomaton(modim_web_server, action_manager, position_manager, arm=arm, alevel=alevel)

    # Define and add states to the automaton
    steady_state = SteadyState(automaton, timeout=wtime)
    # moving_state = MovementTimeoutState(automaton)
    moving_state = MovingState(automaton)
    ask_state = AskState(automaton, timeout=wtime)
    hold_hand_state = HoldHandState(automaton, timeout=wtime)
    quit_state = QuitState(automaton)

    for state in [steady_state, moving_state, ask_state, hold_hand_state, quit_state]:
        automaton.add_state(state)

    # automaton.start('steady_state')

    return automaton
