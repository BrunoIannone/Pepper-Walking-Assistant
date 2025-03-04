import math
import threading

from automaton import TimeoutState, State, FiniteStateAutomaton
from ..utils.limits import joint_limits
from ..utils.postures import default_posture
import time


# ---------------------------------- States ---------------------------------- #

class SteadyState(TimeoutState):

    def __init__(self, automaton):
        super(SteadyState, self).__init__('steady_state', automaton, timeout=automaton.timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(SteadyState, self).on_enter()
        print("[INFO] Entering Steady State")

        self.automaton.perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        self.automaton.instruct()
        print('[INFO] Giving blind/deaf instructions on how to start')

    def on_event(self, event):
        super(SteadyState, self).on_event(event)
        if event == 'head_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')

class GoalState(TimeoutState):

    def __init__(self, automaton):
        super(GoalState, self).__init__('goal_state', automaton, timeout=3, timeout_event='time_elapsed')

    def on_enter(self):
        super(GoalState, self).on_enter()
        print('[INFO] Entering Goal State')

        # Signaling the user it should step back
        if self.automaton.disability == "blind":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_goal)
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_goal)
        print('[INFO] Signaling the user we reached the goal')

    def on_event(self, event):
        super(GoalState, self).on_event(event)
        if event == 'time_elapsed':
            self.automaton.change_state('quit_state')

class QuitState(State):

    def __init__(self, automaton):
        super(QuitState, self).__init__('quit_state', automaton)

    def on_enter(self):
        super(QuitState, self).on_enter()
        print('[INFO] Entering Quit State')

        # Go back to default position
        self.automaton.perform_movement(joint_values=default_posture)
        print('[INFO] Resetting posture')

        # Signaling the user it should step back
        if self.automaton.disability == "blind":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_disagree)
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_disagree)
        print('[INFO] Signaling the user it should step back')

        self.automaton.release_resources()
        print('[INFO] Releasing resources')

        print("[INFO] Done")
        #exit(1)

    def on_event(self, event):
        super(QuitState, self)

class HoldHandState(TimeoutState):

    def __init__(self, automaton):
        super(HoldHandState, self).__init__('hold_hand_state', automaton, timeout=automaton.timeout, timeout_event='time_elapsed')

    def on_enter(self):
        super(HoldHandState, self).on_enter()
        print('[INFO] Entering Hold Hand State')

        # Behavior

        self.automaton.instruct()
        print('[INFO] Giving blind/deaf instructions on how to start')

    def on_event(self, event):
        super(HoldHandState, self).on_event(event)
        if event == 'head_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')

class AskState(TimeoutState):

    def __init__(self, automaton):
        super(AskState, self).__init__('ask_state', automaton, timeout=automaton.timeout, timeout_event='steady_state')

    def on_enter(self):
        super(AskState, self).on_enter()
        print("[INFO] Entering Ask State")

        if self.automaton.disability == "blind":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_ask_cancel)
            print('[INFO] Asking the user if he wants to cancel the procedure')
        elif self.automaton.disability == "deaf":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_ask_cancel)
            print('[INFO] Showing buttons for the user to choose if he wants to cancel the procedure')

        # result = self.automaton.action_manager.check_status()
        # print('[INFO] Obtained response: ' + result)

        # if result == "failure":
        #     self.automaton.on_event("result_no")
        # else:
        #     self.automaton.on_event("result_yes")

    def on_event(self, event):
        super(AskState, self).on_event(event)
        if event == 'result_yes':
            self.automaton.change_state('quit_state')
        elif event == 'result_no':
            self.automaton.change_state('hold_hand_state')
        elif event == 'head_touched':
            self.automaton.change_state('moving_state')
        elif event == 'time_elapsed':
            self.automaton.change_state('quit_state')
        elif event == 'steady_state':
            self.automaton.change_state('quit_state')

class MovingState(State):

    def __init__(self, automaton, eps=0.2, lin_vel=1):
        super(MovingState, self).__init__('moving_state', automaton)

        self.current_room = None
        self.next_room = None
        self.path_index = 0
        self.total_movement = 10
        self.lin_vel = lin_vel
        self.eps = eps
        self.goal_distance = 10  # Total distance the robot should walk
        self.total_distance_walked = 0  # Track walked distance
        self.last_position = None  # Store last known position

    @classmethod
    def distance(cls, curr, target):
        delta_x = target[0] - curr[0]
        delta_y = target[1] - curr[1]
        return (delta_x ** 2 + delta_y ** 2) ** 0.5

    @classmethod
    def compute_velocity(cls, x_curr, y_curr, x_target, y_target, speed=1.0):

        delta_x = x_target - x_curr
        delta_y = y_target - y_curr
        magnitude = (delta_x ** 2 + delta_y ** 2) ** 0.5

        if magnitude == 0:
            return 0, 0  # Already at the target

        # Normalize and scale
        x_vel = (delta_x / magnitude) * speed
        y_vel = (delta_y / magnitude) * speed

        # Ensure speed is within (0, 1)
        x_vel = max(min(x_vel, 1), -1)
        y_vel = max(min(y_vel, 1), -1)

        return x_vel, y_vel
    
    def monitor_head_touch(self):
        """Continuously check if head has been released while moving."""
        while self.monitoring:
            # Get current position
            position_arr = self.automaton.action_manager.mo_service.getRobotPosition(False)
            current_position = (position_arr[0], position_arr[1])

            # Calculate distance moved
            if self.last_position:
                moved_distance = self.distance(self.last_position, current_position)
                self.total_distance_walked += moved_distance
                self.last_position = current_position

            print("[INFO] Distance walked:"+ str(self.total_distance_walked / self.goal_distance)+" meters")

            # Stop if goal distance reached
            if self.total_distance_walked >= self.goal_distance:
                print("[INFO] Goal reached. Transitioning to goal_state.")
                self.automaton.on_event("goal_reached")
                return

            head_touched = self.automaton.action_manager.is_head_touched()
            if not head_touched:
                print("[INFO] Head released detected. Stopping movement...")
                self.automaton.action_manager.mo_service.stopMove()
                self.automaton.on_event('head_released')
                return

            time.sleep(0.1)  # Prevent CPU overload

    def on_enter(self):
        super(MovingState, self).on_enter()

        print("[INFO] Entering moving state")

        if self.automaton.disability == "blind":
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.blind_walking)
        else:
            self.automaton.modim_web_server.run_interaction(self.automaton.action_manager.deaf_walking)

        self.current_room = self.automaton.position_manager.path[self.path_index]
        self.next_room = (
            self.automaton.position_manager.path[self.path_index + 1]
            if self.path_index + 1 < len(self.automaton.position_manager.path)
            else None
        )

        # Ensure we have a valid next room
        if not self.next_room:
            print("[ERROR] No next room found!")
            return
        
        # Get initial position
        position_arr = self.automaton.action_manager.mo_service.getRobotPosition(False)
        self.last_position = (position_arr[0], position_arr[1])

        # Start movement
        self.automaton.action_manager.mo_service.moveToward(self.lin_vel, 0, 0)


        # curr = self.current_room
        # target = self.next_room
        # x_vel, y_vel = self.compute_velocity(curr.x, curr.y, target.x, target.y)
        # self.automaton.action_manager.mo_service.moveToward(x_vel, y_vel, 0)

        # Start monitoring head touch in a separate thread
        self.monitoring = True
        t = threading.Thread(target=self.monitor_head_touch)
        t.setDaemon(True)  # Python 2 way of setting daemon mode
        t.start()

    def on_event(self, event):
        super(MovingState, self).on_event(event)
        
        if event == 'goal_reached':
            self.automaton.action_manager.mo_service.moveToward(0, 0, 0)  # Stop robot
            self.automaton.change_state('goal_state')

        elif event == 'head_released':
            print("[INFO] Stopping movement and switching to ask_state")
            self.monitoring = False  # Stop monitoring
            self.automaton.change_state('ask_state')
        # if event == 'room_reached':

        #     print('[INFO] Fired room_reached event')
        #     print(time.time())

        #     # Go to the next room
        #     self.path_index += 1

        #     # Check if we reached the goal (we are now currently on the last position in the path)
        #     if self.path_index == len(self.automaton.position_manager.path) - 1:

        #         # current the robot
        #         print("[INFO] currentping the robot")
        #         self.automaton.action_manager.mo_service.moveToward(0, 0, 0)

        #         print("[INFO] Path completed. Transitioning to GoalState.")
        #         self.automaton.change_state('goal_state')

        #     else:
        #         # Re-enter the same state
        #         self.automaton.change_state('moving_state')

        # elif event == 'head_released':

        #     print('[INFO] Fired head_released event')

        #     # Stop the robot
        #     self.automaton.action_manager.mo_service.stopMove()

        #     self.automaton.change_state('ask_state')

class RobotAutomaton(FiniteStateAutomaton):

    def __init__(self,
                 modim_web_server,
                 action_manager,
                 position_manager,
                 disability=0,
                 timeout=60,
                 default_lin_vel=0.15
                 ):
        super(RobotAutomaton, self).__init__()
        self.modim_web_server = modim_web_server
        self.action_manager = action_manager
        self.position_manager = position_manager
        self.disability = disability
        self.timeout = timeout
        self.default_lin_vel = default_lin_vel

        # Connect the touch event to the automata
        touch_event = "MiddleTactilTouched"
        self.touch_subscriber = self.action_manager.me_service.subscriber(touch_event)
        self.touch_id = self.touch_subscriber.signal.connect(self.on_head_touch_change)

    # ----------------------------- Utility functions ---------------------------- #

    def on_head_touch_change(self, value):
        """
        Callback function triggered when the head touch event occurs.
        Dispatch the event to the automata.
        """
        print("[INFO] Head touch value changed: " + str(value))
        if value == 0.0:
            self.on_event('head_released')
        else:
            self.on_event('head_touched')

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
        print("[INFO] Instructing (" + self.disability + ") user")
        if self.disability == "blind":
            self.modim_web_server.run_interaction(self.action_manager.blind_walk_hold_head)
        else:
            self.modim_web_server.run_interaction(self.action_manager.deaf_walk_hold_head)
    
    def release_resources(self):
        self.touch_subscriber.signal.disconnect(self.touch_id)

def create_automaton(modim_web_server, action_manager, position_manager, **kwargs):

    automaton = RobotAutomaton(
        modim_web_server,
        action_manager,
        position_manager,
        **kwargs
    )

    # Define and add states to the automaton
    steady_state = SteadyState(automaton)
    moving_state = MovingState(automaton)
    ask_state = AskState(automaton)
    hold_hand_state = HoldHandState(automaton)
    goal_state = GoalState(automaton)
    quit_state = QuitState(automaton)

    for state in [steady_state, moving_state, ask_state, hold_hand_state, goal_state, quit_state]:
        automaton.add_state(state)

    return automaton
