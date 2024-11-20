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

class MovementTimeoutState(TimeoutState):
    def __init__(self, automaton):
        super(MovementTimeoutState, self).__init__(
            'moving_state',
            automaton,
            timeout=10,
            timeout_event='node_reached'
        )

        self.velocity = self.automaton.action_manager.lin_vel
        self.start_time = None
        self.remaining_time = 10
        self.movement_timer = None
        current_x, current_y, theta = self.automaton.action_manager.action_manager.mo_service.getRobotPosition(True)
        next_room = self.automaton.position_manager.get_next_room()

        if next_room:
            self.distance = math.sqrt(
                (next_room.x - current_x) ** 2 +
                (next_room.y - current_y) ** 2
            )
            self.remaining_time = abs(self.distance / self.velocity)

    def on_enter(self):
        if self.movement_timer:
            self.movement_timer.cancel()
            self.movement_timer = None

        print("Starting/Resuming movement with remaining time:", self.remaining_time)
        self.start_time = datetime.now()
        self.automaton.action_manager.set_speed(self.remaining_time)

        self.movement_timer = threading.Timer(self.remaining_time, self._on_timeout)
        self.movement_timer.start()

    def on_event(self, event):
        super(MovementTimeoutState, self).on_event(event)

        if event == 'hand_released':
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.remaining_time = max(0, self.remaining_time - elapsed)

            self.automaton.action_manager.stop_motion()
            if self.movement_timer:
                self.movement_timer.cancel()
                self.movement_timer = None

            print("Movement interrupted. Remaining time:", self.remaining_time)
            self.automaton.change_state('ask_state')

        elif event == 'node_reached':
            print("Node reached")

            if self.movement_timer:
                self.movement_timer.cancel()
                self.movement_timer = None

            next_target = self.automaton.position_manager.get_next_target()
            if next_target is None:
                print("Path completed")
                self.automaton.change_state('quit_state')
            else:
                current_x, current_y, theta = self.automaton.mo_service.getRobotPosition(True)
                next_distance = math.sqrt(
                    (next_target.x - current_x) ** 2 +
                    (next_target.y - current_y) ** 2
                )

                self.initialize_movement(next_distance)
                self.automaton.change_state('moving_state')

    def _on_timeout(self):
        self.automaton.on_event('node_reached')

    def __del__(self):
        if self.movement_timer:
            self.movement_timer.cancel()
            self.movement_timer = None


class MovingState(State):

    def __init__(self, automaton):
        super(MovingState, self).__init__('moving_state', automaton)

        self.current_room = None
        self.next_room = None
        self.path_index = 0

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
                  "Moving from " + str(self.current_room) + " to " + str(self.next_room) + ". " +
                  "Remaining time: " + str(self.remaining_time)
            )

        self.start_timer(self.remaining_time)

        v_x, v_y, omega_z = self.compute_velocity(0.7, 0.3)
        self.automaton.action_manager.mo_service.move(v_x, v_y, omega_z)

    def on_event(self, event):
        super(MovingState, self).on_event(event)

        if event == 'room_reached':

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

        self.start_time = time.time()

        def trigger_event():
            print("[INFO] Triggering `room_reached` event.")
            self.on_event("room_reached")

        self.move_timer = threading.Timer(duration, trigger_event)
        self.move_timer.start()

    def compute_velocity(self, v_max, omega_max):

        # Unpack current and next points
        x_c, y_c = self.current_room.x, self.current_room.y
        x_n, y_n = self.next_room.x, self.next_room.y

        # Compute the differences
        delta_x = x_n - x_c
        delta_y = y_n - y_n
        theta = math.atan2(delta_y, delta_x)
        d = math.sqrt(delta_x ** 2 + delta_y ** 2)

        # Linear velocities
        if d > 0:
            v_x = v_max * (delta_x / d)
            v_y = v_max * (delta_y / d)
        else:
            v_x = 0
            v_y = 0

        # Angular velocity
        # TODO fix this
        delta_theta = 0

        # Normalize to [-pi, pi]
        delta_theta = (delta_theta + math.pi) % (2 * math.pi) - math.pi
        omega_z = max(-omega_max, min(delta_theta, omega_max))

        return v_x, v_y, omega_z

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
        if self.automaton.alevel == 0:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_goal)
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_goal)
        print('[INFO] Signaling the user we reached the target')

        self.automaton.release_resources()
        print('[INFO] Releasing resources')

        print("[INFO] Done")

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

        # Behavior
        # TODO problem here
        if self.automaton.alevel == 0:  # Blindness
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_ask_cancel)
            print('[INFO] Asking the user if he wants to cancel the procedure')
        elif self.automaton.alevel == 1:
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
        self.action_manager.mo_service.setStiffnesses(["LArm", "RArm"], 1.0)

        # Perform movement
        for joint_name, joint_value in joint_values.items():
            if joint_limits[joint_name][0] <= joint_value <= joint_limits[joint_name][1]:
                self.action_manager.mo_service.setAngles(joint_name, joint_value, speed, _async=_async)

        time.sleep(2)

        # Disable arm stiffness during walking
        self.action_manager.mo_service.setStiffnesses(["LArm", "RArm"], 0.0)

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
